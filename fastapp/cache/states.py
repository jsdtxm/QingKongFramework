from typing import TYPE_CHECKING, Dict, Union

from fastapp.cache.base import BaseCache

if TYPE_CHECKING:
    from redis.asyncio import Redis

# 主要为了兼容RedisCache
connections: Dict[str, Union["Redis", "BaseCache"]] = {}


backends: Dict[str, Union["Redis", "BaseCache"]] = {}

caches: Dict[str, "LazyCache"] = {}


class LazyCache:
    def __init__(self, alias: str = "default"):
        self.alias = alias

    @property
    def cache(self, *args, **kwargs) -> BaseCache:
        return backends[self.alias]

    def __getattr__(self, name: str):
        return self.cache.__getattribute__(name)


cache: BaseCache = LazyCache()


class CachesManager:
    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        if key not in self._data:
            self._data[key] = LazyCache(key)
        return self._data[key]


caches = CachesManager()
