import asyncio
from collections import defaultdict
from datetime import date, datetime
from typing import Any, Callable, Dict, Iterable, Optional, Self, Tuple, Type

from pydantic import (
    BaseModel,
    model_serializer,
    model_validator,
)
from pydantic._internal import _model_construction
from pydantic.main import IncEx
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
from libs.utils.functional import copy_method_signature


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

    @copy_method_signature(PydanticModel.model_dump)
    def model_dump(
        self, exclude: IncEx | None = None, exclude_write_only=True, **kwargs
    ) -> dict[str, Any]:
        exclude = exclude or []
        if exclude_write_only:
            exclude = exclude + self.write_only_fields()
        return super().model_dump(exclude=exclude, **kwargs)

    @classmethod
    def read_only_fields(cls):
        return cls.model_config["read_only_fields"]

    @classmethod
    def write_only_fields(cls):
        return cls.model_config["write_only_fields"]

    @classmethod
    def hidden_fields(cls):
        return cls.model_config["hidden_fields"]

    @classmethod
    def orig_model(cls) -> Type[BaseDBModel]:
        return cls.model_config["orig_model"]

    @classmethod
    def model_description(cls) -> Dict[str, Any]:
        return cls.model_config["model_description"]

    async def save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
        force_create: bool = False,
        force_update: bool = False,
        **extra_fields,
    ):
        m2m_fields = self.model_description().get("m2m_fields", [])
        backward_fk_fields = self.model_description().get("backward_fk_fields", [])

        instance = self.orig_model()(
            **(
                self.model_dump(
                    exclude=self.read_only_fields()
                    + [x["name"] for x in m2m_fields]
                    + [x["name"] for x in backward_fk_fields],
                    exclude_unset=True,
                    exclude_write_only=False,
                )
                | extra_fields
            )  # type: ignore[call-arg]
        )

        await instance.save(using_db, update_fields, force_create, force_update)

        m2m_objects = await self._build_related_objects(m2m_fields, using_db=using_db)
        for f in m2m_fields:
            related_objects = m2m_objects.get(f["name"])
            if not related_objects:
                continue

            await asyncio.gather(
                *[getattr(instance, f["name"]).add(obj) for obj in related_objects]
            )

        await self._build_related_objects(
            backward_fk_fields, related_pk=instance.id, using_db=using_db
        )

        return instance

    async def _build_related_objects(
        self, fields, related_pk=None, using_db: Optional[BaseDBAsyncClient] = None
    ):
        result = defaultdict(list)
        for field in fields:
            value = getattr(self, field["name"], None)
            related_model: BaseDBModel = field["python_type"]

            if value is None:
                continue

            if isinstance(value, Iterable) and len(value):
                if isinstance(value[0], ModelSerializerPydanticModel):
                    if related_pk:
                        relation_field = (
                            self.orig_model()
                            ._meta.fields_map[field["name"]]
                            .relation_field
                        )

                    related_objects = []
                    for sub_value in value:
                        if related_pk:
                            related_object = sub_value.save(
                                using_db=using_db, **{relation_field: related_pk}
                            )
                        else:
                            related_object = sub_value.save(using_db=using_db)

                        related_objects.append(related_object)

                    result[field["name"]] = await asyncio.gather(*related_objects)
                else:
                    result[field["name"]] = await related_model.objects.using_db(
                        using_db
                    ).filter(id__in=value)

        return result

    class Config:
        @staticmethod
        def json_schema_extra(schema: dict, cls):
            props = {
                k: v
                for k, v in schema.get("properties", {}).items()
                if k not in cls.hidden_fields() and k not in cls.write_only_fields()
            }

            schema["properties"] = props


def remove_hidden_fields_builder(fields):
    @model_validator(mode="before")
    def remove_hidden_fields(self):
        for field in fields:
            if field in self:
                self.pop(field)

        return self

    return remove_hidden_fields


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

            # TODO 添加一个validator来移除掉不需要的属性
            if hidden_fields or read_only_fields:
                validators_map["remove_hidden_fields"] = remove_hidden_fields_builder(
                    hidden_fields
                )

            if write_only_fields:
                pass

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

    # hidden_fields = 用户不可传递，由程序计算得出

    pass
