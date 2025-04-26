from fastapi_cache import FastAPICache

from common.settings import settings
from fastapp.cache import caches, connections
from fastapp.utils.module_loading import import_string


async def init_cache():
    for alias, config in settings.CACHES.items():
        backend: str = config["BACKEND"]
        backend_class = import_string(backend)

        if backend.endswith("RedisCache"):
            from redis import asyncio as aioredis

            conn = aioredis.from_url(config["LOCATION"])
        elif backend.endswith("DiskCache"):
            import diskcache

            conn = diskcache.Cache(directory=config["DIRECTORY"])
        elif backend.endswith("PostgresBackend"):
            import asyncpg

            conn = await asyncpg.connect(dsn=config["LOCATION"])
        else:
            raise Exception(f"Unknown Backend {backend}")

        connections[alias] = conn

        if alias == "default":
            cache_class = FastAPICache
        else:
            cache_class = type("", (FastAPICache,), {})

        cache_class.init(
            backend_class(conn),
            prefix="qk",
            expire=3600,
            cache_status_header="X-QingKong-Cache",
        )
        caches[alias] = cache_class
