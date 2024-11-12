from typing import Tuple, Type

from pydantic._internal import _model_construction
from pydantic._internal._decorators import (
    FieldValidatorDecoratorInfo,
    ModelValidatorDecoratorInfo,
    PydanticDescriptorProxy,
)
from tortoise.contrib.pydantic.base import PydanticModel
from tortoise.fields.base import Field

from libs.models.base import BaseModel, ModelMetaClass
from libs.serializers.creator import pydantic_model_creator


class SerializerMetaclass(_model_construction.ModelMetaclass):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        if fields_map := dict(filter(lambda x: isinstance(x[1], Field), attrs.items())):
            validators_map = dict(
                filter(
                    lambda x: isinstance(x[1], PydanticDescriptorProxy)
                    and (
                        isinstance(x[1].decorator_info, ModelValidatorDecoratorInfo)
                        or isinstance(x[1].decorator_info, FieldValidatorDecoratorInfo)
                    ),
                    attrs.items(),
                )
            )

            model = ModelMetaClass(
                name,
                (BaseModel,),
                {
                    **fields_map,
                    "PydanticMeta": type(
                        "PydanticMeta", (), {"include": fields_map.keys()}
                    ),
                },
            )

            try:
                pydantic_model = pydantic_model_creator(
                    model, validators=validators_map
                )
                return pydantic_model
            except Exception as e:
                print("ERROR", e)

        return super().__new__(mcs, name, bases, attrs)


class Serializer(PydanticModel, metaclass=SerializerMetaclass):
    pass
