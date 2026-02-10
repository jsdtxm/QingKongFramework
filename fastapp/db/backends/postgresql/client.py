import asyncio
from typing import Any, cast
from tortoise.backends.base.client import (
    PoolConnectionWrapper as BasePoolConnectionWrapper,
    T_conn,
)

# HACK copy from tortoise-orm v1.0.0
class PoolConnectionWrapper(BasePoolConnectionWrapper):
    """Class to manage acquiring from and releasing connections to a pool."""

    __slots__ = ("client", "connection", "_pool_init_lock")

    def __init__(self, client: Any, pool_init_lock: asyncio.Lock) -> None:
        self.client = client
        self.connection: T_conn | None = None
        self._pool_init_lock = pool_init_lock

    async def ensure_connection(self) -> None:
        if not self.client._pool:
            # a safeguard against multiple concurrent tasks trying to initialize the pool
            async with self._pool_init_lock:
                if not self.client._pool:
                    await self.client.create_connection(with_db=True)

    async def __aenter__(self) -> T_conn:
        await self.ensure_connection()
        # get first available connection. If none available, wait until one is released
        self.connection = await self.client._pool.acquire()
        return cast(T_conn, self.connection)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # release the connection back to the pool
        await self.client._pool.release(self.connection)
