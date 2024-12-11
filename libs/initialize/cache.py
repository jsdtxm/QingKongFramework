from fastapi_cache import FastAPICache
from redis import asyncio as aioredis

from common.settings import settings
from libs.cache import RedisCache, caches, connections


def init_cache():
    for alias, config in settings.CACHES.items():
        redis = aioredis.from_url(config["LOCATION"])
        connections[alias] = redis

        if alias == "default":
            cache_class = FastAPICache
        else:
            cache_class = type("", (FastAPICache,), {})

        cache_class.init(
            RedisCache(redis),
            prefix="qk",
            expire=3600,
            cache_status_header="X-QingKong-Cache",
        )
        caches[alias] = cache_class
