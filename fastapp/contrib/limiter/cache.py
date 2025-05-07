import time
from typing import Annotated, Any, AnyStr, Callable, Dict, Optional, Tuple

from pydantic import Field
from starlette.requests import Request
from starlette.responses import Response
from starlette.websockets import WebSocket

from fastapp.cache import caches
from fastapp.cache.base import BaseCache
from fastapp.contrib.limiter.base import BaseRateLimiter

lua_sha_dict: Dict[Tuple[AnyStr, AnyStr], Any] = {}


class CacheRateLimiter(BaseRateLimiter):
    connection: BaseCache

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
        self.connection = caches[self.connection_alias]

    async def _check(self, key):
        # 将毫秒转换为秒
        window_seconds = self.milliseconds / 1000.0

        # 获取当前缓存数据：[时间戳, 计数]
        data = await self.connection.get(key, [time.time(), 0])
        current_time = time.time()

        # 计算已过去的时间
        elapsed_time = current_time - data[0]

        if elapsed_time > window_seconds:
            # 如果当前时间超过窗口，则重置计数器
            data = [current_time, 1]
            await self.connection.set(key, data, timeout=window_seconds)
        else:
            if data[1] >= self.times:
                return (window_seconds - elapsed_time) * 1000
            data[1] += 1
            await self.connection.set(key, data, timeout=window_seconds)

        return 0

    async def __call__(self, request: Request, response: Response):
        if not self.connection:
            raise Exception("Cache connection Invalid")

        key = await self.get_key(request)
        pexpire = await self._check(key)

        if pexpire != 0:
            callback = self.callback or self.http_callback
            return await callback(request, response, pexpire)


class WebSocketCacheRateLimiter(CacheRateLimiter):
    async def __call__(self, ws: WebSocket, context_key=""):
        if not self.connection:
            raise Exception("Cache connection Invalid")

        rate_key = await self.identifier(ws)
        key = f"{self.prefix}:ws:{rate_key}:{context_key}"
        pexpire = await self._check(key)

        if pexpire != 0:
            callback = self.callback or self.ws_callback
            return await callback(ws, pexpire)
