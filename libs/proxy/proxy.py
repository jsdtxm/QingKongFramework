import re
from dataclasses import dataclass

import aiohttp
import aiohttp.web


@dataclass
class ProxyLocation:
    path: str
    target: str
    rewrite: tuple[str, str]

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


PROXY_RULES = [
    ProxyLocation.prefix_proxy("main", "http://127.0.0.1:18001"),
    ProxyLocation.prefix_proxy("user", "http://127.0.0.1:18002"),
]


def handler_factory(proxy_location: ProxyLocation):
    async def handler(request: aiohttp.web.Request):
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=proxy_location.construct_target_url(request.path_qs),
                headers=request.headers,
                data=await request.read(),
            ) as response:
                content = await response.read()

                return aiohttp.web.Response(
                    body=content, status=response.status, headers=response.headers
                )

    return handler


app = aiohttp.web.Application()

app.add_routes(
    [
        aiohttp.web.get(r"/main/{path:.*}", handler_factory(PROXY_RULES[0])),
        aiohttp.web.get(r"/user/{path:.*}", handler_factory(PROXY_RULES[1])),
    ]
)

if __name__ == "__main__":
    aiohttp.web.run_app(app)
