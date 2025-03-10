from fastapi_cache import FastAPICache

from common.settings import settings
from libs.cache import caches, connections
from libs.utils.module_loading import import_string


def init_cache():
    for alias, config in settings.CACHES.items():
        backend: str = config["BACKEND"]
        backend_class = import_string(backend)

        if backend.endswith("RedisCache"):
            from redis import asyncio as aioredis

            conn = aioredis.from_url(config["LOCATION"])
        elif backend.endswith("PostgresBackend"):
            import asyncpg

            conn = asyncpg.create_pool(dsn=config["LOCATION"])
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
