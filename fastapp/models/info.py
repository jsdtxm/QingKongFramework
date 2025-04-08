from typing import TYPE_CHECKING

from tortoise.models import MetaInfo as TortoiseMetaInfo
from tortoise.models import Model

from fastapp.models.base import Manager

if TYPE_CHECKING:
    from fastapp.apps import AppConfig


class MetaInfo(TortoiseMetaInfo):
    __slots__ = TortoiseMetaInfo.__slots__ + ("external", "ignore_schema", "app_config")

    def __init__(self, meta: "Model.Meta") -> None:
        self.external: bool = getattr(meta, "external", False)
        self.ignore_schema: bool = getattr(meta, "ignore_schema", self.external)
        self.app_config: AppConfig = getattr(meta, "app_config", None)
        super().__init__(meta)
        # Override manager
        self.manager: Manager = getattr(meta, "manager", Manager())
