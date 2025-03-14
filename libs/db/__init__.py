from tortoise import connections as tortoise_connections
from tortoise import transactions as transaction
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.router import router

from libs import models


class ConnectionsWrapper:
    def __init__(self, connections):
        self.connections = connections

    def __getitem__(self, key) -> BaseDBAsyncClient:
        conn = self.connections.get(key)
        if conn is None:
            raise KeyError

        return conn

    def get(self, key):
        return self.connections.get(key)

    def keys(self):
        return self.connections.db_config.keys()


connections = ConnectionsWrapper(tortoise_connections)
