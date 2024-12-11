from fastapi_cache.backends.redis import RedisBackend as RedisCache

from libs.cache.redis import get_redis_connection
from libs.cache.states import caches, connections
