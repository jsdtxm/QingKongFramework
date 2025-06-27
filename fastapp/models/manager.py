from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Self,
    Type,
)

from tortoise.expressions import Q
from tortoise.manager import Manager as TortoiseManager
from tortoise.queryset import MODEL

from fastapp.models.queryset import QuerySet

if TYPE_CHECKING:
    from fastapp.models.base import BaseModel


class Manager(Generic[MODEL], TortoiseManager):
    _model: "BaseModel"
    _queryset_class: Type["QuerySet"] = QuerySet

    def __init__(self, model=None) -> None:
        self._model = model

    @classmethod
    def from_queryset(cls, queryset_class, class_name=None):
        if class_name is None:
            class_name = "%sFrom%s" % (cls.__name__, queryset_class.__name__)
        return type(
            class_name,
            (cls,),
            {
                "_queryset_class": queryset_class,
            },
        )

    async def create(self, *args, **kwargs):
        return await self._model.create(*args, **kwargs)

    async def get_or_create(self, *args, **kwargs):
        return await self._model.get_or_create(*args, **kwargs)

    def get_queryset(self) -> QuerySet[MODEL]:
        return self._queryset_class(self._model)

    def __getattr__(self, item):
        attr = getattr(self.get_queryset(), item, None)
        if attr is None:
            return getattr(self._model, item)
        return attr

    if TYPE_CHECKING:

        def all(self) -> "QuerySet[MODEL]": ...

        @classmethod
        def filter(cls, *args: Q, **kwargs: Any) -> QuerySet[Self]: ...
