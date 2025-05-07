import asyncio
from typing import Annotated, Any, AnyStr, Callable, Dict, Optional, Tuple

import redis as pyredis
from pydantic import Field
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from fastapp.cache import get_redis_connection
from fastapp.contrib.limiter.base import BaseRateLimiter

lua_sha_dict: Dict[Tuple[AnyStr, AnyStr], Any] = {}


class RedisRateLimiter(BaseRateLimiter):
    lua_script = """local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire_time = ARGV[2]

local current = tonumber(redis.call('get', key) or "0")
if current > 0 then
 if current + 1 > limit then
 return redis.call("PTTL",key)
 else
        redis.call("INCR", key)
 return 0
 end
else
    redis.call("SET", key, 1,"px",expire_time)
 return 0
end"""

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
        super().__init__(
            times=times,
            milliseconds=milliseconds,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            identifier=identifier,
            callback=callback,
            connection_alias=connection_alias,
        )
        self.connection = get_redis_connection(self.connection_alias)

        asyncio.create_task(self.script_load())

    async def script_load(self):
        self.lua_sha = lua_sha_dict.get(
            (self.connection_alias, self.lua_script),
            await self.connection.script_load(self.lua_script),
        )

    async def _check(self, key):
        pexpire = await self.connection.evalsha(
            self.lua_sha, 1, key, str(self.times), str(self.milliseconds)
        )
        return pexpire

    async def __call__(self, request: Request, response: Response):
        if not self.connection:
            raise Exception("Redis connection Invalid")

        callback = self.callback or self.http_callback
        key = await self.get_key(request)

        try:
            pexpire = await self._check(key)
        except pyredis.exceptions.NoScriptError:
            self.lua_sha = await self.connection.script_load(self.lua_script)
            pexpire = await self._check(key)

        if pexpire != 0:
            return await callback(request, response, pexpire)


class WebSocketRedisRateLimiter(RedisRateLimiter):
    async def __call__(self, ws: WebSocket, context_key=""):
        if not self.connection:
            raise Exception("Redis connection Invalid")
        
        rate_key = await self.identifier(ws)

        key = f"{self.prefix}:ws:{rate_key}:{context_key}"
        pexpire = await self._check(key)
        callback = self.callback or self.ws_callback
        if pexpire != 0:
            return await callback(ws, pexpire)
