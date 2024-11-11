from tortoise.backends import sqlite
from tortoise.backends.sqlite import schema_generator

from .mixin import SchemaGeneratorMixin


class SqliteSchemaGenerator(
    SchemaGeneratorMixin, schema_generator.SqliteSchemaGenerator
):
    pass


class SqliteClient(sqlite.SqliteClient):
    schema_generator = SqliteSchemaGenerator


client_class = SqliteClient
