from typing import TYPE_CHECKING, Dict

from fastapp.cache.base import BaseCache

if TYPE_CHECKING:
    from redis.asyncio import Redis

connections: Dict["Redis" | "BaseCache"] = {}
caches: Dict["Redis" | "BaseCache"] = {}


class LazyCache:
    @property
    def cache(self, *args, **kwargs) -> BaseCache:
        return caches["default"]


cache: BaseCache = LazyCache.cache
