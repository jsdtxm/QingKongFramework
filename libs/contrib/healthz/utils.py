from tortoise import Tortoise

from libs.cache import connections as cache_connections
from libs.db import connections as db_connections


async def check_db_and_cache():
    checks = {}
    status_code = 200

    # DB
    for alias in db_connections.keys():
        try:
            cursor = db_connections[alias]
            await cursor.execute_query("SELECT 1;")
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"db {alias} error: {str(e)}"
            status_code = 500

    await Tortoise.close_connections()

    # Cache
    for alias, conn in cache_connections.items():
        try:
            await conn.info()
            checks["cache"] = "ok"
        except Exception as e:
            checks["cache"] = f"cache {alias} error: {str(e)}"
            status_code = 500

    return checks, status_code
