import logging
import logging.config
import os
import re
from collections import Counter
from functools import lru_cache
from urllib.parse import urlparse

import aiohttp
import aiohttp.client_exceptions
import aiohttp.web
import click
import uvloop

from common.settings import settings
from fastapp.initialize.apps import init_apps
from fastapp.logging import generate_app_logging_config
from fastapp.misc.aiohttp_utils import (
    aiohttp_print_override,
    error_middleware,
    log_middleware,
)

logging.config.dictConfig(generate_app_logging_config("gateway"))
access_logger = logging.getLogger("qingkong.access")
error_logger = logging.getLogger("qingkong.error")

debug_flag = False


class ProxyLocation:
    prefix: str
    path: str
    target: str
    rewrite: tuple[str, str]

    def __init__(
        self, path, target, rewrite, add_slashes=False, fastapi_redirect=False
    ):
        self.path = path
        self.target = target
        self.rewrite = rewrite

        self.prefix = s.groups(1)[0] if (s := re.search(r"^/(\S+)/\{", path)) else ""

        self.add_slashes = add_slashes
        self.fastapi_redirect = fastapi_redirect

    def __repr__(self):
        return (
            f"ProxyLocation {self.prefix}/* -> {self.target}; Rewrite: {self.rewrite}"
        )

    def log(self):
        return f"ProxyLocation {click.style(f'{self.prefix}/*', fg='bright_blue')} -> {click.style(self.target, fg='bright_cyan')}; Rewrite: {click.style(self.rewrite, fg='magenta')}"

    @classmethod
    def prefix_proxy(cls, prefix, target, add_slashes=False, fastapi_redirect=False):
        if prefix == "":
            return cls(
                r"/{path:.*}",
                target,
                (r"^/(.*)$", r"/$1"),
                add_slashes=add_slashes,
                fastapi_redirect=fastapi_redirect,
            )

        return cls(
            r"/" + prefix + r"/{path:.*}",
            target,
            (r"^/" + prefix + r"/(.*)$", r"/$1"),
            add_slashes=add_slashes,
            fastapi_redirect=fastapi_redirect,
        )

    def rewrite_path(self, path):
        return re.sub(self.rewrite[0], re.sub(r"\$(\d)", r"\\1", self.rewrite[1]), path)

    def construct_target_url(self, path):
        new_path = self.rewrite_path(path)
        if self.add_slashes and not new_path.endswith("/"):
            new_path = new_path + "/"

        return self.target + new_path

    def to_aiohttp_route(self):
        return aiohttp.web.route("*", self.path, handler_factory(self))


def swagger_proxy_middleware(
    proxy_loc: ProxyLocation, request: aiohttp.web.Request, content: bytes
):
    if re.match(rf"^/{proxy_loc.prefix}/docs", request.path):
        content = re.sub(
            rb"url:\s*\'(/openapi.json)\'", b"url: './openapi.json'", content
        )
    elif re.match(rf"^/{proxy_loc.prefix}/openapi.json", request.path):
        content = (
            content[:-1]
            + b',"servers": [{"url": "/'
            + proxy_loc.prefix.encode()
            + b'","description": "Default server"}]}'
        )

    return content


@lru_cache
def check_origin(origin: str | None, referer: str | None):
    if origin:
        origin = origin.replace("/", "")
        if any(map(lambda x: origin.endswith(x), settings.ALLOWED_HOSTS)):
            return True
    elif referer:
        referer = referer.replace("/", "")
        if any(map(lambda x: origin.endswith(x), settings.ALLOWED_HOSTS)):
            return True

    return False


def create_new_headers(headers):
    new_headers = {
        k: v
        for k, v in headers.items()
        if k.lower() != "content-length" and k.lower() != "transfer-encoding"
    }
    return new_headers


def parse_forwarded_for(request: aiohttp.web.Request):
    peername = request.transport.get_extra_info("peername")

    client_ip = peername[0] if peername else "unknown"
    # 处理X-Forwarded-For头部
    headers = request.headers.copy()
    xff = headers.get("X-Forwarded-For", "")
    if xff:
        xff += ", " + client_ip
    else:
        xff = client_ip
    headers["X-Forwarded-For"] = xff

    return headers


def handler_factory(proxy_loc: ProxyLocation):
    async def handler(request: aiohttp.web.Request):
        async with aiohttp.ClientSession() as session:
            request_url = proxy_loc.construct_target_url(request.path_qs)
            request_content = await request.read()

            headers = parse_forwarded_for(request)

            async with session.request(
                method=request.method,
                url=request_url,
                headers=headers,
                allow_redirects=False,
                data=request_content,
            ) as response:
                content = await response.read()

                if response.status == 307:
                    if location := response.headers.get("Location"):
                        parsed_url = urlparse(location)

                        if proxy_loc.fastapi_redirect:
                            parsed_request_url = urlparse(request_url)
                            response = await session.request(
                                method=request.method,
                                url=parsed_request_url._replace(
                                    path=parsed_url.path,
                                    query=parsed_url.query,
                                    fragment=parsed_url.fragment,
                                    params=parsed_url.params,
                                ).geturl(),
                                headers=headers,
                                allow_redirects=False,
                                data=await request.read(),
                            )

                            content = await response.read()
                        else:
                            parsed_url = parsed_url._replace(
                                path=f"/{proxy_loc.prefix}" + parsed_url.path
                            )

                            headers = create_new_headers(response.headers)
                            headers["Location"] = parsed_url.geturl()

                            return aiohttp.web.Response(
                                body=content, status=response.status, headers=headers
                            )

                content = swagger_proxy_middleware(proxy_loc, request, content)

                headers = create_new_headers(response.headers)

                if settings.ADD_CORS_HEADERS:
                    origin = request.headers.get("Origin", "")
                    referer = request.headers.get("Referer", "")

                    if check_origin(origin, referer):
                        headers["Access-Control-Allow-Origin"] = origin or referer
                        headers["Access-Control-Allow-Credentials"] = "true"
                        headers["Access-Control-Allow-Headers"] = "Content-Type"

                if debug_flag:
                    print(request_content)
                    print(content)

                return aiohttp.web.Response(
                    body=content, status=response.status, headers=headers
                )

    return handler


def run_gateway(
    host="127.0.0.1",
    port=8000,
    upstream_dict={},
    default_upstream="127.0.0.1",
    add_slashes=False,
    fastapi_redirect=False,
    debug=False,
):
    global debug_flag

    debug_flag = debug

    apps = init_apps(settings.INSTALLED_APPS)

    app_configs = [
        x
        for x in apps.app_configs.values()
        if x.has_module("urls") and x.name not in settings.NO_EXPORT_APPS
    ]

    proxy_rules = [
        ProxyLocation.prefix_proxy(
            v.prefix,
            f"http://{upstream_dict.get(v.prefix, default_upstream)}:{v.port}",
            add_slashes=add_slashes,
            fastapi_redirect=fastapi_redirect,
        )
        for v in app_configs
    ]

    # Extra proxy
    proxy_rules.extend(
        [
            ProxyLocation.prefix_proxy(
                p[0],
                p[1],
                add_slashes=add_slashes,
                fastapi_redirect=fastapi_redirect,
            )
            for p in settings.EXTRA_PROXY
        ]
    )

    prefix_counter = Counter([rule.prefix for rule in proxy_rules])
    for _, count in prefix_counter.items():
        if count > 1:
            raise Exception("Prefix duplicate")

    error_logger.info("Gateway proxy rules:")
    for p in proxy_rules:
        error_logger.info(p.log())

    proxy_app = aiohttp.web.Application(middlewares=[log_middleware, error_middleware])

    proxy_app.add_routes([r.to_aiohttp_route() for r in proxy_rules])
    error_logger.info(
        f"Gateway running on {click.style(f'http://{host}:{port}', fg='bright_white')} (Press CTRL+C to quit)"
    )
    error_logger.info(f"Started server process [{click.style(os.getpid(), fg='blue')}]")
    error_logger.info("Waiting for application startup.")

    aiohttp.web.run_app(
        proxy_app,
        host=host,
        port=port,
        loop=uvloop.new_event_loop(),
        print=aiohttp_print_override,
    )


if __name__ == "__main__":
    run_gateway()
