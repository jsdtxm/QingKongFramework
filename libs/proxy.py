import re

import aiohttp
import aiohttp.web
import uvloop

from common.settings import settings
from libs.initialize.apps import init_apps


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
        return f"ProxyLocation {self.prefix}/* -> {self.target}; Rewrite: {self.rewrite}"

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


PROXY_RULES = [
    ProxyLocation.prefix_proxy("polypro", "http://127.0.0.1:18001"),
    ProxyLocation.prefix_proxy("user", "http://127.0.0.1:18002"),
]


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
                }

                return aiohttp.web.Response(
                    body=content, status=response.status, headers=headers
                )

    return handler


def run_proxy(host="127.0.0.1", port=8000):
    apps = init_apps(settings.INSTALLED_APPS)

    proxy_rules = [
        ProxyLocation.prefix_proxy(v.label, f"http://127.0.0.1:{v.port}")
        for v in apps.app_configs.values()
    ]

    print("proxy_rules:")
    for p in proxy_rules:
        print(p)

    proxy_app = aiohttp.web.Application()

    proxy_app.add_routes([r.to_aiohttp_route() for r in proxy_rules])
    aiohttp.web.run_app(proxy_app, host=host, port=port, loop=uvloop.new_event_loop())


if __name__ == "__main__":
    run_proxy()
