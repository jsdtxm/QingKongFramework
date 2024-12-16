from tortoise.models import MetaInfo as TortoiseMetaInfo
from tortoise.models import Model


class MetaInfo(TortoiseMetaInfo):
    __slots__ = TortoiseMetaInfo.__slots__ + ("external", "ignore_schema")

    def __init__(self, meta: "Model.Meta") -> None:
        self.external: bool = getattr(meta, "external", False)
        self.ignore_schema: bool = getattr(meta, "ignore_schema", self.external)
        super().__init__(meta)
