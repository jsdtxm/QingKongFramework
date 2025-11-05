from fastapi_cache import FastAPICache

from common.settings import settings
from fastapp.cache.states import backends, connections
from fastapp.utils.module_loading import import_string


class FastAPICacheWrapper(FastAPICache):
    @classmethod
    def __getattribute__(cls, name):
        if name in {"get", "set", "sync_get", "sync_set"} and hasattr(
            cls._backend, name
        ):
            return getattr(cls._backend, name)
        raise AttributeError(f"Attribute {name} not found in {cls.__name__}")


async def init_cache():
    for alias, config in settings.CACHES.items():
        backend: str = config["BACKEND"]

        if backend.endswith("RedisCache"):
            from redis import asyncio as aioredis

            conn = aioredis.from_url(config["LOCATION"])
        elif backend.endswith("DiskCacheBackend"):
            from fastapp.cache.disk import DiskCacheBackend

            conn = DiskCacheBackend(
                directory=config["DIRECTORY"],
                timeout=int(config.get("TIMEOUT", 60)),
                disk=import_string(f"diskcache.{config.get('DISK', 'Disk')}"),
                params=config.get("OPTIONS", {}),
            )
        elif backend.endswith("PostgresBackend"):
            import asyncpg

            conn = await asyncpg.connect(dsn=config["LOCATION"])
        else:
            raise Exception(f"Unknown Backend {backend}")

        if backend.endswith("DiskCacheBackend"):
            # HACK
            backends[alias] = conn
            continue
        else:
            connections[alias] = conn

        if alias == "default":
            cache_class = FastAPICacheWrapper
        else:
            cache_class = type(alias, (FastAPICacheWrapper,), {})

        backend_class = import_string(backend)

        cache_class.init(
            backend_class(conn),
            prefix="fastapp",
            expire=3600,
            cache_status_header="X-FastApp-Cache",
        )
        backends[alias] = cache_class
