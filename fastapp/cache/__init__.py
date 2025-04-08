from fastapi_cache.backends.redis import RedisBackend as RedisCache

try:
    from fastapp.cache.postgres.backend import PostgresBackend as PostgresBackend
except ImportError:
    pass
from fastapp.cache.redis import get_redis_connection
from fastapp.cache.states import caches, connections
