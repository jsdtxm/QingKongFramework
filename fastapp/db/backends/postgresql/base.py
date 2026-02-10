from __future__ import annotations
import asyncio
from typing import Any, SupportsInt

from tortoise.backends.asyncpg.client import AsyncpgDBClient as TortoiseAsyncpgDBClient
from tortoise.backends.base.client import ConnectionWrapper
from tortoise.backends.base_postgres.client import translate_exceptions

from fastapp.db.backends.postgresql.client import PoolConnectionWrapper

# HACK copy from tortoise-orm v1.0.0
class AsyncpgDBClient(TortoiseAsyncpgDBClient):
    def __init__(
        self,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        host: str | None = None,
        port: SupportsInt = 5432,
        **kwargs: Any,
    ) -> None:
        super().__init__(user, password, database, host, port, **kwargs)

        self._pool_init_lock = asyncio.Lock()

    def acquire_connection(self) -> ConnectionWrapper | PoolConnectionWrapper:
        return PoolConnectionWrapper(self, self._pool_init_lock)

    @translate_exceptions
    async def execute_query(
        self, query: str, values: list | None = None
    ) -> tuple[int, list[dict]]:
        async with self.acquire_connection() as connection:
            self.log.debug("%s: %s", query, values)
            if values:
                params = [query, *values]
            else:
                params = [query]
            normalized = query.lstrip().upper()
            if (
                normalized.startswith("UPDATE")
                or normalized.startswith("DELETE")
                or normalized.startswith("INSERT")
            ):
                res = await connection.execute(*params)
                try:
                    rows_affected = int(res.split(" ")[1])
                except Exception:  # pragma: nocoverage
                    rows_affected = 0
                return rows_affected, []

            rows = await connection.fetch(*params)
            return len(rows), rows
