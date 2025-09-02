from typing import Any, Optional, SupportsInt

from tortoise.backends import asyncpg
from tortoise.backends.asyncpg import schema_generator

from fastapp.db.backends.mixin import SchemaGeneratorMixin


class PostgreSQLSchemaGenerator(
    SchemaGeneratorMixin, schema_generator.AsyncpgSchemaGenerator
):
    pass


class PostgreSQLClient(asyncpg.AsyncpgDBClient):
    schema_generator = PostgreSQLSchemaGenerator

    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        host: Optional[str] = None,
        port: SupportsInt = 5432,
        **kwargs: Any,
    ) -> None:
        if "charset" in kwargs:
            kwargs.pop("charset")
        if "configure" in kwargs:
            kwargs["init"] = kwargs.pop("configure")
        super().__init__(user, password, database, host, port, **kwargs)

    async def _translate_exceptions(self, func, *args, **kwargs) -> Exception:
        try:
            return await func(self, *args, **kwargs)
        finally:
            await self._expire_connections()


client_class = PostgreSQLClient
