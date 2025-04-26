from fastapp.cache.base import BaseCache

connections = {}
caches = {}


class LazyCache:
    @property
    def cache(self, *args, **kwargs) -> BaseCache:
        return caches["default"]


cache: BaseCache = LazyCache.cache
