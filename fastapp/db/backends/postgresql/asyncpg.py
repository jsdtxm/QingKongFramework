from typing import Any, Optional, SupportsInt

from fastapp.db.backends.postgresql.base import AsyncpgDBClient
from tortoise.backends.asyncpg import schema_generator

from fastapp.db.backends.mixin import SchemaGeneratorMixin
from fastapp.db.backends.postgresql.executor import AsyncpgExecutor


class PostgreSQLSchemaGenerator(
    SchemaGeneratorMixin, schema_generator.AsyncpgSchemaGenerator
):
    pass


class PostgreSQLClient(AsyncpgDBClient):
    executor_class = AsyncpgExecutor
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


client_class = PostgreSQLClient
