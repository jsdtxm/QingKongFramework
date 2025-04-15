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
from tortoise.transactions import in_transaction

from fastapp.models.base import BaseModel as BaseDBModel
from fastapp.serializers.base import (
    BaseSerializer,
    get_serializer_map,
    get_serializers_map_from_fields,
    get_validators_map,
)
from fastapp.serializers.creator import pydantic_model_creator
from fastapp.utils.context import BlankContextManager
from fastapp.utils.functional import copy_method_signature


class ModelSerializerPydanticModel(PydanticModel):
    _instance: Optional[BaseDBModel] = None
    _instance_processed: bool = False

    def __init__(self, /, null: bool = False, **data: Any) -> None:
        super().__init__(**data)

        self._field_config = {}  # store property config when serializer as a field
        self._field_config["null"] = null

    @model_serializer(mode="wrap")
    def serialize(
        self, original_serializer: Callable[[Self], dict[str, Any]]
    ) -> dict[str, Any]:
        result = original_serializer(self)
        # TODO 或许不再需要，直接放到response阶段处理

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

    def to_model(self, **extra_fields):
        if self._instance_processed:
            return self._instance

        model_description = self.model_description()
        data_fields = model_description.get("data_fields", [])
        pk_field = model_description.get("pk_field", None)
        raw_instance_fields = data_fields + (
            [
                pk_field,
            ]
            if pk_field
            else []
        )

        m2m_fields = model_description.get("m2m_fields", [])
        backward_fk_fields = model_description.get("backward_fk_fields", [])

        self._instance = self.orig_model()(
            **(
                (
                    {
                        x["name"]: getattr(self._instance, x["name"])
                        for x in raw_instance_fields
                    }
                    if self._instance
                    else {}
                )
                | self.model_dump(
                    exclude=self.read_only_fields()
                    + [x["name"] for x in m2m_fields]
                    + [x["name"] for x in backward_fk_fields],
                    exclude_unset=True,
                    exclude_write_only=False,
                )
                | extra_fields
            )  # type: ignore[call-arg]
        )
        if self._instance.pk is not None:
            self._instance._saved_in_db = True

        self._instance_processed = True

        return self._instance

    async def save(
        self,
        using_db: Optional[BaseDBAsyncClient] = None,
        update_fields: Optional[Iterable[str]] = None,
        force_create: bool = False,
        force_update: bool = False,
        is_in_transaction: bool = False,
        **extra_fields,
    ):
        m2m_fields = self.model_description().get("m2m_fields", [])
        backward_fk_fields = self.model_description().get("backward_fk_fields", [])

        instance = self.to_model(**extra_fields)

        transaction_context_manager = (
            BlankContextManager if is_in_transaction else in_transaction
        )

        async with transaction_context_manager(instance.app.default_connection):
            await instance.save(using_db, update_fields, force_create, force_update)

            m2m_objects = await self._build_related_objects(
                m2m_fields, using_db=using_db
            )

            for f in m2m_fields:
                field = getattr(instance, f["name"])
                await field.clear()

                related_objects = m2m_objects.get(f["name"])
                if not related_objects:
                    continue

                for obj in related_objects:
                    await field.add(obj)

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
                                using_db=using_db,
                                is_in_transaction=True,
                                **{relation_field: related_pk},
                            )
                        else:
                            related_object = sub_value.save(
                                using_db=using_db, is_in_transaction=True
                            )

                        related_objects.append(related_object)

                    result[field["name"]] = await asyncio.gather(*related_objects)
                else:
                    result[field["name"]] = await related_model.objects.filter(
                        id__in=value
                    ).using_db(using_db)

        return result

    def update(self, data: dict) -> Self:
        self.__dict__.update(data)
        return self

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
                name=f"{attrs['__module__']}.{name}",
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


# FIXME 不支持继承
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
