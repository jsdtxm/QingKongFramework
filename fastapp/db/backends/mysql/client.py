from tortoise.backends import mysql

from fastapp.db.backends.mysql.executor import MySQLExecutor
from fastapp.db.backends.mysql.schema_generator import MySQLSchemaGenerator


class MySQLClient(mysql.MySQLClient):
    schema_generator = MySQLSchemaGenerator
    executor_class = MySQLExecutor
