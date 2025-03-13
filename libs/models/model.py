from typing import TYPE_CHECKING, Any, Type

from . import fields
from .base import BaseMeta, BaseModel


class Model(BaseModel):
    id = fields.BigIntegerField(primary_key=True)

    class Meta(BaseMeta):
        """Model Meta"""

        abstract = True

    if TYPE_CHECKING:
        # 避免子类 type hint 报错
        Meta: Type[Any]
        PydanticMeta: Type[Any]
        StubGenMeta: Type[Any]
