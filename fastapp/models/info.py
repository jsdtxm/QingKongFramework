from typing import TYPE_CHECKING

from tortoise.models import MetaInfo as TortoiseMetaInfo
from tortoise.models import Model

from fastapp.models.manager import Manager

if TYPE_CHECKING:
    from fastapp.apps import AppConfig


class MetaInfo(TortoiseMetaInfo):
    __slots__ = TortoiseMetaInfo.__slots__ + (
        "external",
        "managed",
        "ignore_schema",
        "app_config",
    )

    def __init__(self, meta: "Model.Meta") -> None:
        self.external: bool = getattr(meta, "external", False)
        self.managed: bool = getattr(meta, "managed", True)
        self.ignore_schema: bool = getattr(meta, "ignore_schema", self.external)
        self.app_config: AppConfig = getattr(meta, "app_config", None)
        super().__init__(meta)
        # Override manager
        self.manager: Manager = getattr(meta, "manager", Manager())

    @property
    def is_managed(self) -> bool:
        return self.external is False and self.managed is True

    def data_fields(self, serializable: bool = True) -> list:
        return [
            field.describe(serializable)
            for name, field in self.fields_map.items()
            if name != self.pk_attr and name in (self.fields - self.fetch_fields)
        ]

    # FIXME 这里不会用到router的路径
    # @property
    # def db(self) -> BaseDBAsyncClient:
    #     if self.default_connection is None:
    #         print("[db]", self.default_connection)
    #         raise ConfigurationError(
    #             f"default_connection for the model {self._model} cannot be None"
    #         )
    #     return connections.get(self.default_connection)
