from typing import Tuple, Type

from pydantic._internal import _model_construction
from tortoise.contrib.pydantic.base import PydanticModel


class SerializerMetaclass(_model_construction.ModelMetaclass):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        return super().__new__(mcs, name, bases, attrs)


class Serializer(PydanticModel, metaclass=SerializerMetaclass):
    pass
