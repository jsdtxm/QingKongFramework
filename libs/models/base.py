from typing import Any, Union

from tortoise.manager import Manager as TortoiseManager
from tortoise.models import Model as TortoiseModel
from tortoise.queryset import QuerySet

from . import fields


class Manager(TortoiseManager):
    _model: TortoiseModel

    def create(self, *args, **kwargs):
        return self._model.create(*args, **kwargs)


class Model(TortoiseModel):
    id = fields.BigIntField(primary_key=True)
    objects: Union[Manager, QuerySet] = Manager()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    class Meta:
        manager = Manager()
