from typing import Any, Optional, SupportsInt

from tortoise.backends import asyncpg
from tortoise.backends.asyncpg import schema_generator

from .mixin import SchemaGeneratorMixin


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
        kwargs.pop("charset")
        super().__init__(user, password, database, host, port, **kwargs)


client_class = PostgreSQLClient
