from typing import TYPE_CHECKING, Dict, Union

from fastapp.cache.base import BaseCache

if TYPE_CHECKING:
    from redis.asyncio import Redis

connections: Dict[str, Union["Redis", "BaseCache"]] = {}
caches: Dict[str, Union["Redis", "BaseCache"]] = {}


class LazyCache:
    @property
    def cache(self, *args, **kwargs) -> BaseCache:
        return caches["default"]


cache: BaseCache = LazyCache.cache
