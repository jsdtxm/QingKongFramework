from typing import Iterable, Optional, Tuple, Type, Any, Callable, Self

from pydantic import (
    BaseModel,
    model_serializer,
)
from pydantic._internal import _model_construction
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.contrib.pydantic.base import PydanticModel
from tortoise.fields import Field

from libs.models.base import BaseModel as BaseDBModel
from libs.serializers.base import (
    BaseSerializer,
    get_serializer_map,
    get_serializers_map_from_fields,
    get_validators_map,
)
from libs.serializers.creator import pydantic_model_creator
from datetime import datetime, date


class ModelSerializerPydanticModel(PydanticModel):
    @model_serializer(mode="wrap")
    def serialize(
        self, original_serializer: Callable[[Self], dict[str, Any]]
    ) -> dict[str, Any]:
        result = original_serializer(self)

        for k, v in result.items():
            if isinstance(v, datetime):
                result[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(v, date):
                result[k] = v.strftime("%Y-%m-%d")

        return result
    
    @property
    def read_only_fields(self):
        return self.model_config["read_only_fields"]

    @property
    def orig_model(self) -> Type[BaseDBModel]:
        return self.model_config["orig_model"]

    async def save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
        force_create: bool = False,
        force_update: bool = False,
    ):
        instance = self.orig_model(**self.model_dump(exclude=self.read_only_fields))
        await instance.save(using_db, update_fields, force_create, force_update)


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
            read_only_fields = getattr(meta, "read_only_fields", ())
            write_only_fields = getattr(meta, "write_only_fields", ())
            hidden_fields = getattr(meta, "hidden_fields", ())

            if fields == "__all__":
                fields = ()

            extra_fields = {
                name: value
                for name, value in attrs.items()
                if isinstance(value, BaseModel) or isinstance(value, Field)
            }

            validators_map = get_validators_map(attrs)
            serializers_map = get_serializer_map(
                attrs
            ) | get_serializers_map_from_fields(extra_fields)

            pydantic_model = pydantic_model_creator(
                meta.model,
                name=name,
                bases=ModelSerializerPydanticModel,
                extra_fields=extra_fields,
                include=fields,
                exclude=exclude,
                read_only_fields=read_only_fields,
                write_only_fields=write_only_fields,
                hidden_fields=hidden_fields,
                validators=validators_map | serializers_map,
                depth=getattr(meta, "depth", 0),
            )

            return pydantic_model

        return super().__new__(mcs, name, bases, attrs)


class ModelSerializer(
    BaseSerializer, ModelSerializerPydanticModel, metaclass=ModelSerializerMetaclass
):
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
