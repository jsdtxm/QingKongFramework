from typing import TYPE_CHECKING, Optional, Type

from tortoise.router import ConnectionRouter as TortoiseConnectionRouter

from libs.models import Model

if TYPE_CHECKING:
    from tortoise import BaseDBAsyncClient


class ConnectionRouter(TortoiseConnectionRouter):
    def _db_route(self, model: Type["Model"], action: str):
        try:
            return self.db_route(model)
        except NotImplementedError:
            return super()._db_route(model, action)
    
    def db_route(self, model: Type["Model"]) -> Optional["BaseDBAsyncClient"]:
        raise NotImplementedError
        
    def db_for_read(self, model: Type["Model"]) -> Optional["BaseDBAsyncClient"]:  # type: ignore
        return self._db_route(model, "db_for_read")

    def db_for_write(self, model: Type["Model"]) -> Optional["BaseDBAsyncClient"]:  # type: ignore
        return self._db_route(model, "db_for_write")
