from tortoise.backends import mysql
from tortoise.backends.mysql import schema_generator

from .mixin import SchemaGeneratorMixin


class MySQLSchemaGenerator(SchemaGeneratorMixin, schema_generator.MySQLSchemaGenerator):
    pass


class MySQLClient(mysql.MySQLClient):
    schema_generator = MySQLSchemaGenerator


client_class = MySQLClient
