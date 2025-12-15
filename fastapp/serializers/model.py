import asyncio
from collections import defaultdict
from datetime import date, datetime
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Self,
    Tuple,
    Type,
    Union,
)

from pydantic import BaseModel, ValidationInfo, model_validator
from pydantic._internal import _model_construction
from pydantic.main import IncEx
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.contrib.pydantic.base import PydanticModel
from tortoise.fields import Field
from tortoise.fields.relational import BackwardFKRelation
from tortoise.transactions import in_transaction

from fastapp.conf import settings
from fastapp.models.base import BaseModel as BaseDBModel
from fastapp.models.base import QuerySet
from fastapp.serializers.base import (
    BaseSerializer,
    get_serializer_map,
    get_serializers_map_from_fields,
    get_validators_map,
)
from fastapp.serializers.creator import pydantic_model_creator
from fastapp.utils.context import BlankContextManager
from fastapp.utils.functional import copy_method_signature

try:
    from fastapp.models.fields.vector import VectorField
except ImportError:
    VectorField = None


def _get_fetch_fields(
    pydantic_class: "Type[PydanticModel]", model_class: "Type[BaseDBModel]"
) -> List[str]:
    """
    Recursively collect fields needed to fetch
    :param pydantic_class: The pydantic model class
    :param model_class: The tortoise model class
    :return: The list of fields to be fetched
    """
    fetch_fields = []
    for field_name, field_type in pydantic_class.__annotations__.items():
        origin = getattr(field_type, "__origin__", None)
        if origin in (list, List, Union):
            field_type = field_type.__args__[0]

        # noinspection PyProtectedMember
        sub_origin = getattr(field_type, "__origin__", None)
        if sub_origin is Union:
            field_type = field_type.__args__[0]

        if field_name in model_class._meta.fetch_fields and issubclass(
            field_type, PydanticModel
        ):
            subclass_fetch_fields = _get_fetch_fields(
                field_type, field_type.model_config["orig_model"]
            )
            if subclass_fetch_fields:
                fetch_fields.extend(
                    [field_name + "__" + f for f in subclass_fetch_fields]
                )
            else:
                fetch_fields.append(field_name)
    return fetch_fields


class ModelSerializerPydanticModel(PydanticModel):
    _instance: Optional[BaseDBModel] = None
    _instance_processed: bool = False

    _meta = None

    def __new__(cls, *args, null: bool = False, **kwargs):
        if null:
            return cls.model_construct()

        instance = super().__new__(cls)
        return instance

    def __init__(self, /, null: bool = False, **data: Any) -> None:
        if not null:
            super().__init__(**data)

        self._field_config = {}  # store property config when serializer as a field
        self._field_config["null"] = null

    # @model_serializer(mode="wrap")
    # def serialize(
    #     self, original_serializer: Callable[[Self], dict[str, Any]]
    # ) -> dict[str, Any]:
    #     """
    #     FUCK, 这会导致pydantic的serialization模式触发回退机制
    #     已弃用，在后续流程中处理
    #     """
    #     result = original_serializer(self)

    #     for k, v in result.items():
    #         if isinstance(v, datetime):
    #             result[k] = v.strftime("%Y-%m-%d %H:%M:%S")
    #         elif isinstance(v, date):
    #             result[k] = v.strftime("%Y-%m-%d")

    #     return result

    @copy_method_signature(PydanticModel.model_dump)
    def model_dump(
        self, exclude: IncEx | None = None, exclude_write_only=True, **kwargs
    ) -> dict[str, Any]:
        exclude = exclude or []
        if exclude_write_only:
            if isinstance(exclude, set):
                exclude = list(exclude)
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

    @classmethod
    def field_map(cls) -> Dict[str, Any]:
        return cls.model_config["field_map"]

    @classmethod
    def nested_fields(cls) -> Dict[str, Any]:
        return {
            field: config
            for field, config in cls.model_config["field_map"].items()
            if config.get("nested_field")
        }

    async def to_model(self, **extra_fields):
        if self._instance_processed:
            return self._instance

        model_description = self.model_description()

        data_fields = model_description.get("data_fields", [])
        pk_fields = (
            [
                pk_field,
            ]
            if (pk_field := model_description.get("pk_field", None))
            else []
        )
        raw_instance_fields = data_fields + pk_fields

        m2m_fields = model_description.get("m2m_fields", [])
        o2o_fields = model_description.get("o2o_fields", [])
        fk_fields = model_description.get("fk_fields", [])
        backward_fk_fields = model_description.get("backward_fk_fields", [])

        exclude_fields = set(
            self.read_only_fields()
            + [x["name"] for x in m2m_fields]
            + [x["name"] for x in o2o_fields]
            + [x["name"] for x in fk_fields]
            + [x["name"] for x in backward_fk_fields]
        ) - {"id"}

        if getattr(self, "id", None):
            # 允许嵌套的部分更新
            related_model = self.orig_model()
            obj = await related_model.get(id=self.id)
            model_data = {
                k: getattr(obj, k)
                for k in [x["name"] for x in related_model._meta.data_fields()]
            }
        else:
            model_data = {}

        model_data = model_data | (
            (
                {
                    x["name"]: getattr(self._instance, x["name"])
                    for x in raw_instance_fields
                }
                if self._instance
                else {}
            )
            | self.model_dump(
                exclude=exclude_fields,
                exclude_unset=True,
                exclude_write_only=False,
            )  # type: ignore[call-arg]
            | extra_fields
        )  # type: ignore[call-arg]

        self._instance = self.orig_model()(**model_data)

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

        # print("[self]", self)
        instance = await self.to_model(**extra_fields)

        transaction_context_manager = (
            BlankContextManager if is_in_transaction else in_transaction
        )

        async with transaction_context_manager(instance.app.default_connection):
            # TODO 这里需要识别创建的情况
            # print("[instance]", instance, instance.id, update_fields, force_create, force_update)
            await instance.save(using_db, update_fields, force_create, force_update)

            m2m_objects = await self._build_related_objects(
                m2m_fields, using_db=using_db
            )

            # FIXME 更新时可能导致m2m字段丢失
            for f in m2m_fields:
                field = getattr(instance, f["name"])
                await field.clear()

                related_objects = m2m_objects.get(f["name"])
                if not related_objects:
                    continue

                for obj in related_objects:
                    await field.add(obj)

            await self._build_related_objects(
                backward_fk_fields, related_instance=instance, using_db=using_db
            )
        return instance

    async def _build_related_objects(
        self,
        fields,
        related_instance=None,
        using_db: Optional[BaseDBAsyncClient] = None,
    ):
        # TODO 不支持嵌套的更新
        field_map = self.field_map()
        result = defaultdict(list)
        for field in fields:
            value = getattr(self, field["name"], None)

            if value is None:
                continue

            related_model: BaseDBModel = field["python_type"]
            field_desc = field_map.get(field["name"])

            if isinstance(value, Iterable) and len(value):
                model_field_type = self.orig_model()._meta.fields_map[field["name"]]

                related_objects = []
                for sub_value in value:
                    if isinstance(sub_value, ModelSerializerPydanticModel):
                        sub_model_id = getattr(sub_value, "id", None)

                        if not sub_model_id:
                            if not field_desc.get("writable", False):
                                raise ValueError(
                                    f"Field '{field['name']}' not allow nested create"
                                )

                            if related_instance:
                                related_object = sub_value.save(
                                    using_db=using_db,
                                    is_in_transaction=True,
                                    **{
                                        model_field_type.relation_field: related_instance.id
                                    },
                                )
                            else:
                                related_object = sub_value.save(
                                    using_db=using_db, is_in_transaction=True
                                )
                        else:
                            if field["field_type"] is BackwardFKRelation:
                                # HACK 有限地允许反向FK的更新
                                related_object = sub_value.save(
                                    using_db=using_db, is_in_transaction=True
                                )
                            else:
                                # FIXME 这个地方是导致m2m异常clear的原因，目前使用了以下的to_model方式来绕过
                                related_object = sub_value.to_model()

                        related_objects.append(related_object)
                    else:
                        if isinstance(sub_value, dict):
                            if sub_object_id := sub_value.get("id", None):
                                sub_value = sub_object_id
                            else:
                                raise ValueError(
                                    f"Not support this value '{sub_value}'"
                                )
                        related_objects.append(
                            await related_model.objects.get(id=sub_value).using_db(
                                using_db
                            )
                        )

                all_related_objects = await asyncio.gather(*related_objects)
                result[field["name"]] = all_related_objects

                if isinstance(model_field_type, BackwardFKRelation):
                    model_field = getattr(related_instance, field["name"], None)
                    await (
                        model_field.all()
                        .exclude(id__in=[x.id for x in all_related_objects])
                        .delete()
                    )

        return result

    def update(self, data: dict) -> Self:
        new_data = self.model_dump() | data
        new_serializer = self.__class__(**new_data)

        for key in data:
            setattr(self, key, getattr(new_serializer, key))

        return self

    @classmethod
    async def from_tortoise_orm(cls, obj: "BaseDBModel") -> Self:
        """
        Returns a serializable pydantic model instance built from the provided model instance.

        .. note::

            This will prefetch all the relations automatically. It is probably what you want.

            If you don't want this, or require a ``sync`` method, look to using ``.from_orm()``.

            In that case you'd have to manage  prefetching yourself,
            or exclude relational fields from being part of the model using
            :class:`tortoise.contrib.pydantic.creator.PydanticMeta`, or you would be
            getting ``OperationalError`` exceptions.

            This is due to how the ``asyncio`` framework forces I/O to happen in explicit ``await``
            statements. Hence we can only do lazy-fetching during an awaited method.

        :param obj: The Model instance you want serialized.
        """
        # Get fields needed to fetch
        fetch_fields = _get_fetch_fields(cls, cls.model_config["orig_model"])  # type: ignore
        # Fetch fields
        await obj.fetch_related(*fetch_fields)
        return cls.model_validate(obj)

    @classmethod
    async def from_queryset(cls, queryset: "QuerySet") -> List[Self]:
        """
        Returns a serializable pydantic model instance that contains a list of models,
        from the provided queryset.

        This will prefetch all the relations automatically.

        :param queryset: a queryset on the model this PydanticModel is based on.
        """
        fetch_fields = _get_fetch_fields(cls, cls.model_config["orig_model"])  # type: ignore
        return [
            cls.model_validate(e)
            for e in await queryset.prefetch_related(*fetch_fields)
        ]

    class Config:
        @staticmethod
        def json_schema_extra(schema: dict, cls):
            props = {
                k: v
                for k, v in schema.get("properties", {}).items()
                if k not in cls.hidden_fields() and k not in cls.write_only_fields()
            }

            schema["properties"] = props

        json_encoders = {
            datetime: lambda v: v.strftime(settings.DATETIME_FORMAT),
            date: lambda v: v.strftime(settings.DATE_FORMAT),
        }


def remove_hidden_fields_builder(fields):
    @model_validator(mode="before")
    def remove_hidden_fields(self, values: ValidationInfo):
        # TODO 这个函数到底用来干啥的我完全不记得了
        if isinstance(self, type) and issubclass(self, BaseModel):
            return values

        if isinstance(self, BaseDBModel):
            return self

        if values.data is None:
            return self

        if not isinstance(self, dict):
            return self

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

            # HACK exclude VectorField
            for k, v in meta.model._meta.fields_map.items():
                if VectorField and isinstance(v, VectorField):
                    exclude += (k,)

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

            pydantic_model._meta = meta

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
