from fastapi_cache.backends.redis import RedisBackend as RedisCache

try:
    from libs.cache.postgres.backend import PostgresBackend as PostgresBackend
except ImportError:
    pass
from libs.cache.redis import get_redis_connection
from libs.cache.states import caches, connections
