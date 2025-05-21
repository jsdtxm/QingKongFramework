import asyncio
from typing import TYPE_CHECKING

import diskcache

from fastapp.cache.base import DEFAULT_TIMEOUT, BaseCache
from fastapp.utils.functional import cached_property


class DiskCacheBackend(BaseCache):
    """DiskCache is a simple in-memory cache implementation."""

    def __init__(self, directory=None, timeout=60, disk=diskcache.Disk, params={}):
        super().__init__(params)

        self._class = diskcache.Cache

        self._directory = directory
        self._timeout = timeout
        self._disk = disk
        self._options = params.get("OPTIONS", {})

        self.loop = asyncio.get_running_loop()

    @cached_property
    def _cache(self) -> diskcache.Cache:
        return self._class(self._directory, self._timeout, self._disk, **self._options)

    if TYPE_CHECKING:

        @property  # type: ignore[no-redef]
        def _cache(self) -> diskcache.Cache: ...

    async def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        return await self.loop.run_in_executor(
            None, self._cache.add, key, value, self.get_backend_timeout(timeout)
        )

    async def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        return await self.loop.run_in_executor(None, self._cache.get, key, default)

    def sync_get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        return self._cache.get(key, default)

    async def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        await self.loop.run_in_executor(None, self._cache.set, key, value, timeout)

    def sync_set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        self._cache.set(key, value, timeout)

    async def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        return await self.loop.run_in_executor(
            None, self._cache.touch, key, self.get_backend_timeout(timeout)
        )

    async def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        return await self.loop.run_in_executor(None, self._cache.delete, key)

    async def incr(self, key, delta=1, version=None):
        key = self.make_key(key, version=version)
        return await self.loop.run_in_executor(None, self._cache.incr, key, delta)

    async def clear(self):
        return await self.loop.run_in_executor(None, self._cache.close)
