from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi_cache.types import Backend

import asyncpg


class PostgresBackend(Backend):
    def __init__(self, pool: asyncpg.pool.Pool):
        self.pool = pool

    async def get_with_ttl(self, key: str) -> Tuple[int, Optional[bytes]]:
        query = """
            SELECT value,
                CASE
                    WHEN expire_at IS NULL THEN -1
                    ELSE EXTRACT(epoch FROM (expire_at - NOW()))::integer
                END AS ttl
            FROM _qk_cache
            WHERE key = $1 AND (expire_at IS NULL OR expire_at > NOW())
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, key)
            if row:
                ttl = row["ttl"]
                return (ttl if ttl == -1 else max(0, ttl), row["value"])
            return (0, None)

    async def get(self, key: str) -> Optional[bytes]:
        query = """
            SELECT value FROM _qk_cache
            WHERE key = $1 AND (expire_at IS NULL OR expire_at > NOW())
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, key)
            return row["value"] if row else None

    async def set(self, key: str, value: bytes, expire: Optional[int] = None) -> None:
        expire_at = (
            (datetime.now(timezone.utc) + timedelta(seconds=expire)) if expire else None
        )
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO _qk_cache (key, value, inserted_at, expire_at)
                VALUES ($1, $2, NOW(), $3)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    inserted_at = EXCLUDED.inserted_at,
                    expire_at = EXCLUDED.expire_at
                """,
                key,
                value,
                expire_at,
            )

    async def clear(
        self, namespace: Optional[str] = None, key: Optional[str] = None
    ) -> int:
        async with self.pool.acquire() as conn:
            if namespace:
                rows = await conn.fetch(
                    "DELETE FROM _qk_cache WHERE key LIKE $1 || ':%' RETURNING id",
                    namespace,
                )
                return len(rows)
            elif key:
                rows = await conn.fetch(
                    "DELETE FROM _qk_cache WHERE key = $1 RETURNING id", key
                )
                return len(rows)
            return 0
