import asyncio
from typing import Annotated, Any, AnyStr, Callable, Dict, Optional, Tuple, Type

import redis as pyredis
from pydantic import Field
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from fastapp.cache import get_redis_connection
from fastapp.contrib.limiter import RedisRateLimiter

lua_sha_dict: Dict[Tuple[AnyStr, AnyStr], Any] = {}


class RateLimiter:
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
        limiter: Type[RedisRateLimiter] = RedisRateLimiter,
    ):
        self.times = times
        self.milliseconds = (
            milliseconds + 1000 * seconds + 60000 * minutes + 3600000 * hours
        )
        self.identifier = identifier
        self.callback = callback

        self.connection_alias = connection_alias
        self.connection = get_redis_connection(connection_alias)
        self.limiter = limiter

        asyncio.create_task(self.script_load())

    async def script_load(self):
        self.lua_sha = lua_sha_dict.get(
            (self.connection_alias, self.limiter.lua_script),
            await self.connection.script_load(self.limiter.lua_script),
        )

    async def _check(self, key):
        pexpire = await self.connection.evalsha(
            self.lua_sha, 1, key, str(self.times), str(self.milliseconds)
        )
        return pexpire

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

    async def __call__(self, request: Request, response: Response):
        if not self.connection:
            raise Exception("Redis connection Invalid")

        route_index, dep_index = self.get_dep_index(request)

        # moved here because constructor run before app startup
        identifier = self.identifier or self.limiter.identifier
        callback = self.callback or self.limiter.http_callback
        rate_key = await identifier(request)
        key = f"{self.limiter.prefix}:{rate_key}:{route_index}:{dep_index}"
        try:
            pexpire = await self._check(key)
        except pyredis.exceptions.NoScriptError:
            self.lua_sha = await self.connection.script_load(self.limiter.lua_script)
            pexpire = await self._check(key)
        if pexpire != 0:
            return await callback(request, response, pexpire)


class WebSocketRateLimiter(RateLimiter):
    async def __call__(self, ws: WebSocket, context_key=""):
        if not self.connection:
            raise Exception("Redis connection Invalid")
        identifier = self.identifier or self.limiter.identifier
        rate_key = await identifier(ws)
        key = f"{self.limiter.prefix}:ws:{rate_key}:{context_key}"
        pexpire = await self._check(key)
        callback = self.callback or self.limiter.ws_callback
        if pexpire != 0:
            return await callback(ws, pexpire)
