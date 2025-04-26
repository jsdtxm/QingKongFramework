"Base Cache class."

import time

from fastapp.utils.module_loading import import_string

DEFAULT_TIMEOUT = object()


def default_key_func(key, key_prefix, version):
    """Generate a default cache key by combining key prefix, version and key.

    Args:
        key: The base key for the cache entry
        key_prefix: A prefix to prepend to all keys
        version: The version number of the cache entry

    Returns:
        str: A formatted cache key in the format "prefix:version:key"
    """
    return f"{key_prefix}:{version}:{key}"


def get_key_func(key_func):
    """Get the key generation function for cache keys.

    Args:
        key_func: Either a callable function or an import path string. If None,
                 the default key function will be used.

    Returns:
        callable: A function that generates cache keys. If key_func is callable,
                 returns it directly. If key_func is a string, imports and returns
                 the function. If key_func is None, returns the default key function.
    """
    if key_func is not None:
        if callable(key_func):
            return key_func
        else:
            return import_string(key_func)
    return default_key_func


class BaseCache:
    """Base class for cache implementations.

    This class provides the interface and common functionality for all cache backends.
    It handles key generation, timeout management, and provides default implementations
    for common cache operations that can be overridden by subclasses.

    Subclasses must implement the core cache operations: add, get, set, delete, and clear.
    """

    _missing_key = object()

    def __init__(self, params):
        timeout = params.get("timeout", params.get("TIMEOUT", 300))
        if timeout is not None:
            try:
                timeout = int(timeout)
            except (ValueError, TypeError):
                timeout = 300
        self.default_timeout = timeout

        options = params.get("OPTIONS", {})
        max_entries = params.get("max_entries", options.get("MAX_ENTRIES", 300))
        try:
            self._max_entries = int(max_entries)
        except (ValueError, TypeError):
            self._max_entries = 300

        cull_frequency = params.get("cull_frequency", options.get("CULL_FREQUENCY", 3))
        try:
            self._cull_frequency = int(cull_frequency)
        except (ValueError, TypeError):
            self._cull_frequency = 3

        self.key_prefix = params.get("KEY_PREFIX", "")
        self.version = params.get("VERSION", 1)
        self.key_func = get_key_func(params.get("KEY_FUNCTION"))

    def get_backend_timeout(self, timeout=DEFAULT_TIMEOUT):
        """
        Return the timeout value usable by this backend based upon the provided
        timeout.
        """
        if timeout == DEFAULT_TIMEOUT:
            timeout = self.default_timeout
        elif timeout == 0:
            # ticket 21147 - avoid time.time() related precision issues
            timeout = -1
        return None if timeout is None else time.time() + timeout

    def make_key(self, key, version=None):
        """
        Construct the key used by all other methods. By default, use the
        key_func to generate a key (which, by default, prepends the
        `key_prefix' and 'version'). A different key function can be provided
        at the time of cache construction; alternatively, you can subclass the
        cache backend to provide custom key making behavior.
        """
        if version is None:
            version = self.version

        return self.key_func(key, self.key_prefix, version)

    async def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        """
        Set a value in the cache if the key does not already exist. If
        timeout is given, use that timeout for the key; otherwise use the
        default cache timeout.

        Return True if the value was stored, False otherwise.
        """
        raise NotImplementedError(
            "subclasses of BaseCache must provide an add() method"
        )

    async def get(self, key, default=None, version=None):
        """
        Fetch a given key from the cache. If the key does not exist, return
        default, which itself defaults to None.
        """
        raise NotImplementedError("subclasses of BaseCache must provide a get() method")

    async def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        """
        Set a value in the cache. If timeout is given, use that timeout for the
        key; otherwise use the default cache timeout.
        """
        raise NotImplementedError("subclasses of BaseCache must provide a set() method")

    async def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        """
        Update the key's expiry time using timeout. Return True if successful
        or False if the key does not exist.
        """
        raise NotImplementedError(
            "subclasses of BaseCache must provide a touch() method"
        )

    async def delete(self, key, version=None):
        """
        Delete a key from the cache and return whether it succeeded, failing
        silently.
        """
        raise NotImplementedError(
            "subclasses of BaseCache must provide a delete() method"
        )

    async def get_many(self, keys, version=None):
        """See get_many()."""
        d = {}
        for k in keys:
            val = await self.get(k, self._missing_key, version=version)
            if val is not self._missing_key:
                d[k] = val
        return d

    async def get_or_set(self, key, default, timeout=DEFAULT_TIMEOUT, version=None):
        """See get_or_set()."""
        val = await self.get(key, self._missing_key, version=version)
        if val is self._missing_key:
            if callable(default):
                default = default()
            await self.add(key, default, timeout=timeout, version=version)
            # Fetch the value again to avoid a race condition if another caller
            # added a value between the first aget() and the aadd() above.
            return await self.get(key, default, version=version)
        return val

    async def has_key(self, key, version=None):
        """
        Return True if the key is in the cache and has not expired.
        """
        return (
            await self.get(key, self._missing_key, version=version)
            is not self._missing_key
        )

    async def incr(self, key, delta=1, version=None):
        """See incr()."""
        value = await self.get(key, self._missing_key, version=version)
        if value is self._missing_key:
            raise ValueError(f"Key '{key}' not found")
        new_value = value + delta
        await self.set(key, new_value, version=version)
        return new_value

    async def decr(self, key, delta=1, version=None):
        """
        Subtract delta from value in the cache. If the key does not exist, raise
        a ValueError exception.
        """
        return await self.incr(key, -delta, version=version)

    def __contains__(self, key):
        """
        Return True if the key is in the cache and has not expired.
        """
        # This is a separate method, rather than just a copy of has_key(),
        # so that it always has the same functionality as has_key(), even
        # if a subclass overrides it.
        return self.has_key(key)

    async def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        """
        Set a bunch of values in the cache at once from a dict of key/value
        pairs.  For certain backends (memcached), this is much more efficient
        than calling set() multiple times.

        If timeout is given, use that timeout for the key; otherwise use the
        default cache timeout.

        On backends that support it, return a list of keys that failed
        insertion, or an empty list if all keys were inserted successfully.
        """
        for key, value in data.items():
            await self.set(key, value, timeout=timeout, version=version)
        return []

    async def delete_many(self, keys, version=None):
        """
        Delete a bunch of values in the cache at once. For certain backends
        (memcached), this is much more efficient than calling delete() multiple
        times.
        """
        for key in keys:
            await self.delete(key, version=version)

    async def clear(self):
        """Remove *all* values from the cache at once."""
        raise NotImplementedError(
            "subclasses of BaseCache must provide a clear() method"
        )

    async def incr_version(self, key, delta=1, version=None):
        """See incr_version()."""
        if version is None:
            version = self.version

        value = await self.get(key, self._missing_key, version=version)
        if value is self._missing_key:
            raise ValueError(f"Key '{key}' not found")

        await self.set(key, value, version=version + delta)
        await self.delete(key, version=version)
        return version + delta

    async def decr_version(self, key, delta=1, version=None):
        """
        Subtract delta from the cache version for the supplied key. Return the
        new version.
        """
        return await self.incr_version(key, -delta, version)

    async def close(self, **kwargs):
        """Close the cache connection"""
        pass
