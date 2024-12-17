import logging
import logging.config
import os
import re
from collections import Counter
from functools import lru_cache

import aiohttp
import aiohttp.client_exceptions
import aiohttp.web
import click
import uvloop

from common.settings import settings
from libs.initialize.apps import init_apps
from libs.logging import generate_app_logging_config

logging.config.dictConfig(generate_app_logging_config("gateway"))
access_logger = logging.getLogger("qingkong.access")
error_logger = logging.getLogger("qingkong.error")


class ProxyLocation:
    prefix: str
    path: str
    target: str
    rewrite: tuple[str, str]

    def __init__(self, path, target, rewrite):
        self.path = path
        self.target = target
        self.rewrite = rewrite

        self.prefix = re.search(r"^/(\S+)/\{", path).groups(1)[0]

    def __repr__(self):
        return (
            f"ProxyLocation {self.prefix}/* -> {self.target}; Rewrite: {self.rewrite}"
        )

    def log(self):
        return f"ProxyLocation {click.style(f"{self.prefix}/*", fg="bright_blue")} -> {click.style(self.target, fg="bright_cyan")}; Rewrite: {click.style(self.rewrite, fg="magenta")}"

    @classmethod
    def prefix_proxy(cls, prefix, target):
        return cls(
            r"/" + prefix + r"/{path:.*}",
            target,
            (r"^/" + prefix + r"/(.*)$", r"/$1"),
        )

    def rewrite_path(self, path):
        return re.sub(self.rewrite[0], re.sub(r"\$(\d)", r"\\1", self.rewrite[1]), path)

    def construct_target_url(self, path):
        return self.target + self.rewrite_path(path)

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


def handler_factory(proxy_loc: ProxyLocation):
    async def handler(request: aiohttp.web.Request):
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=proxy_loc.construct_target_url(request.path_qs),
                headers=request.headers,
                data=await request.read(),
            ) as response:
                content = await response.read()
                content = swagger_proxy_middleware(proxy_loc, request, content)

                headers = {
                    k: v
                    for k, v in response.headers.items()
                    if k.lower() != "content-length"
                    and k.lower() != "transfer-encoding"
                }

                if settings.ADD_CORS_HEADERS:
                    origin = request.headers.get("Origin", "")
                    referer = request.headers.get("Referer", "")

                    if check_origin(origin, referer):
                        headers["Access-Control-Allow-Origin"] = origin or referer
                        headers["Access-Control-Allow-Credentials"] = "true"
                        headers["Access-Control-Allow-Headers"] = "Content-Type"

                return aiohttp.web.Response(
                    body=content, status=response.status, headers=headers
                )

    return handler


async def error_middleware(app, handler):
    async def middleware_handler(request: aiohttp.web.Request):
        try:
            return await handler(request)
        except aiohttp.web.HTTPException as ex:
            return aiohttp.web.json_response({"error": str(ex)}, status=ex.status)
        except aiohttp.client_exceptions.ClientConnectorError:
            return aiohttp.web.json_response(
                {
                    "error": "Bad Gateway",
                    "message": "Upstream server is currently unavailable.",
                },
                status=502,
            )
        except Exception as ex:
            return aiohttp.web.json_response(
                {"error": "Internal Server Error", "message": str(ex)}, status=500
            )

    return middleware_handler


async def log_middleware(app, handler):
    async def middleware_handler(request: aiohttp.web.Request):
        response: aiohttp.web.Response = await handler(request)
        access_logger.info(
            '%s - "%s %s HTTP/%s" %d',
            request.remote,
            request.method,
            request.path_qs,
            f"{request.version.major}.{request.version.minor}",
            response.status,
        )
        return response

    return middleware_handler


def aiohttp_print_override(*args, **kwargs):
    error_logger.info("Application startup complete.")


def run_gateway(
    host="127.0.0.1", port=8000, upstream_dict={}, default_upstream="127.0.0.1"
):
    apps = init_apps(settings.INSTALLED_APPS)

    proxy_rules = [
        ProxyLocation.prefix_proxy(
            v.prefix, f"http://{upstream_dict.get(v.prefix, default_upstream)}:{v.port}"
        )
        for v in apps.app_configs.values()
    ]

    # Extra proxy
    proxy_rules.extend(
        [ProxyLocation.prefix_proxy(p[0], p[1]) for p in settings.EXTRA_PROXY]
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
        f"Gateway running on {click.style(f"http://{host}:{port}", fg="bright_white")} (Press CTRL+C to quit)"
    )
    error_logger.info(f"Started server process [{click.style(os.getpid(), fg="blue")}]")
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
