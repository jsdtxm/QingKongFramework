from fastapi_cache.backends.redis import RedisBackend as RedisCache

from libs.cache.postgres.backend import PostgresBackend as PostgresBackend
from libs.cache.redis import get_redis_connection
from libs.cache.states import caches, connections
