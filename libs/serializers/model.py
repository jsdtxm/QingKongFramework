from typing import Tuple, Type

from pydantic import BaseModel
from pydantic._internal import _model_construction
from tortoise.contrib.pydantic.base import PydanticModel
from tortoise.fields import Field

from libs.serializers.creator import pydantic_model_creator


class ModelSerializerMetaclass(_model_construction.ModelMetaclass):
    # TODO
    # read_only_fields = ['account_name']
    # extra_kwargs = {'password': {'write_only': True}}
    # validators = [
    #             UniqueTogetherValidator(
    #                 queryset=Event.objects.all(),
    #                 fields=['room_number', 'date']
    #             )
    #         ]
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        fields, exclude = (), ()

        if meta := attrs.get("Meta", None):
            fields = getattr(meta, "fields", ())
            exclude = getattr(meta, "exclude", ())

            extra_fields = {
                name: value
                for name, value in attrs.items()
                if isinstance(value, BaseModel) or isinstance(value, Field)
            }

            pydantic_model = pydantic_model_creator(
                meta.model,
                name=name,
                extra_fields=extra_fields,
                include=fields,
                exclude=exclude,
            )

            return pydantic_model

        return super().__new__(mcs, name, bases, attrs)


class ModelSerializer(PydanticModel, metaclass=ModelSerializerMetaclass):
    """
    ModelSerializer
    ```python
    class PolyAiDoiSerializer(ModelSerializer):
        class Meta:
            model = ModelName
            fields = (field1, field2)
            exclude = (field1, field2)
    ```
    """

    pass
