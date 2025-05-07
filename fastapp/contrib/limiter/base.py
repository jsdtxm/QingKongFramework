from typing import Annotated, Callable, Optional

from pydantic import Field
from starlette.requests import Request

from fastapp.contrib.limiter.callback import http_default_callback, ws_default_callback
from fastapp.contrib.limiter.utils import ip_identifier


class BaseRateLimiter:
    key_infix: str = "http"

    prefix: Optional[str] = None
    identifier: Optional[Callable] = None
    http_callback: Optional[Callable] = None
    ws_callback: Optional[Callable] = None

    initialized: bool = False

    def __init__(
        self,
        times: Annotated[int, Field(ge=0)] = 1,
        milliseconds: Annotated[int, Field(ge=-1)] = 0,
        seconds: Annotated[int, Field(ge=-1)] = 0,
        minutes: Annotated[int, Field(ge=-1)] = 0,
        hours: Annotated[int, Field(ge=-1)] = 0,
        identifier: Optional[Callable] = None,
        callback: Optional[Callable] = None,
        connection_alias: str = "default",
    ):
        self.times = times
        self.milliseconds = (
            milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours
        )
        if identifier:
            self.identifier = identifier
        self.callback = callback

        self.connection_alias = connection_alias

        if not self.initialized:
            self.init()

    @classmethod
    async def init(
        cls,
        prefix: str = "fastapp-limiter",
        identifier: Callable = ip_identifier,
        http_callback: Callable = http_default_callback,
        ws_callback: Callable = ws_default_callback,
    ) -> None:
        cls.prefix = prefix
        cls.identifier = cls.func_wrap(identifier)
        cls.http_callback = cls.func_wrap(http_callback)
        cls.ws_callback = cls.func_wrap(ws_callback)

        cls.initialized = True

    @staticmethod
    def func_wrap(func):
        def wrapper(_self, *args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def get_dep_index(self, request: Request):
        route_index = 0
        dep_index = 0
        for i, route in enumerate(request.app.routes):
            if route.path == request.scope["path"] and request.method in route.methods:
                route_index = i
                for j, dependency in enumerate(route.dependencies):
                    if self is dependency.dependency:
                        dep_index = j
                        break
        return route_index, dep_index

    async def get_key(self, request: Request) -> str:
        route_index, dep_index = self.get_dep_index(request)

        rate_key = await self.identifier(request)

        return f"{self.prefix}:{self.key_infix}:{rate_key}:{route_index}:{dep_index}"
