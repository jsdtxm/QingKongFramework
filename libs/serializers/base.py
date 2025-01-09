from abc import ABCMeta
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Self, Tuple, Type, Union

import pytz
from pydantic import BaseModel, Field, create_model, field_serializer
from pydantic._internal._decorators import (
    FieldSerializerDecoratorInfo,
    FieldValidatorDecoratorInfo,
    ModelValidatorDecoratorInfo,
    PydanticDescriptorProxy,
)
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaMode,
    JsonSchemaValue,
)
from pydantic.main import IncEx
from pydantic_core import CoreSchema
from tortoise.contrib.pydantic.base import PydanticModel
from tortoise.fields.base import Field as TortoiseField

from libs.serializers.fields import DateTimeField
from libs.utils.functional import classproperty, copy_method_signature
from tortoise.queryset import QuerySet as TortoiseQuerySet


class EmptyModelMetaclass(ModelMetaclass):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        return type.__new__(mcs, name, bases, attrs)


class BoolMeta(type):
    def __bool__(cls):
        return False

class empty(metaclass=BoolMeta):
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """

    def __bool__(self):
        return False


NOT_READ_ONLY_WRITE_ONLY = "May not set both `read_only` and `write_only`"
NOT_READ_ONLY_REQUIRED = "May not set both `read_only` and `required`"
NOT_REQUIRED_DEFAULT = "May not set both `required` and `default`"
USE_READONLYFIELD = "Field(read_only=True) should be ReadOnlyField"
MISSING_ERROR_MESSAGE = (
    "ValidationError raised by `{class_name}`, but error key `{key}` does "
    "not exist in the `error_messages` dictionary."
)


class BaseSerializer:
    if TYPE_CHECKING:

        @property
        def data(self) -> Self:
            return self

        @copy_method_signature(BaseModel.model_dump)
        def model_dump(self, *args, **kwargs): ...

        @copy_method_signature(BaseModel.model_dump_json)
        def model_dump_json(self, *args, **kwargs): ...

        @classmethod
        async def from_queryset(cls, queryset: "TortoiseQuerySet") -> List[Self]: ...

        @classmethod
        def model_validate(
            cls,
            obj: Any,
            *,
            strict: bool | None = None,
            from_attributes: bool | None = None,
            context: Any | None = None,
        ) -> Self: ...


class OverrideMixin:
    def __getattr__(self, item: str) -> Any:
        return object.__getattribute__(self, item)

    def __setattr__(self, name: str, value: Any) -> None:
        return object.__setattr__(self, name, value)


class RestField:
    _creation_counter = 0

    default_error_messages = {
        "required": "This field is required.",
        "null": "This field may not be null.",
    }
    default_validators = []
    initial = None

    def __init__(
        self,
        *,
        read_only=False,
        write_only=False,
        required=None,
        default=empty,
        initial=empty,
        source=None,
        label=None,
        help_text=None,
        style=None,
        error_messages=None,
        validators=None,
        allow_null=False,
    ):
        # If `required` is unset, then use `True` unless a default is provided.
        if required is None:
            required = default is empty and not read_only

        # Some combinations of keyword arguments do not make sense.
        assert not (read_only and write_only), NOT_READ_ONLY_WRITE_ONLY
        assert not (read_only and required), NOT_READ_ONLY_REQUIRED
        assert not (required and default is not empty), NOT_REQUIRED_DEFAULT
        assert not (read_only and self.__class__ == Field), USE_READONLYFIELD

        self.read_only = read_only
        self.write_only = write_only
        self.required = required
        self.default = default
        self.source = source
        self.initial = self.initial if (initial is empty) else initial
        self.label = label
        self.help_text = help_text
        self.style = {} if style is None else style
        self.allow_null = allow_null

        if validators is not None:
            self.validators = list(validators)

        # These are set up by `.bind()` when the field is added to a serializer.
        self.field_name = None
        self.parent = None

        # Collect default error message from self and parent classes
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, "default_error_messages", {}))
        messages.update(error_messages or {})
        self.error_messages = messages


class SerializerModel(
    OverrideMixin, RestField, PydanticModel, metaclass=EmptyModelMetaclass
):
    pydantic_model: Type[BaseModel]

    def __init__(self, instance=None, data=empty, **kwargs):
        if instance:
            self.instance = self.pydantic_model.model_validate(instance)
        else:
            self.instance = instance

        if data is not empty:
            self.initial_data = data
        self.partial = kwargs.pop("partial", False)
        self._context = kwargs.pop("context", {})
        kwargs.pop("many", None)
        super().__init__(**kwargs)

    @property
    def data(self):
        return self

    def __str__(self):
        return object.__str__(self)

    def __repr__(self):
        return object.__repr__(self)

    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        return self.pydantic_model.__pydantic_serializer__.to_python(
            self.instance,
            mode=mode,
            by_alias=by_alias,
            include=include,
            exclude=exclude,
            context=context,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type[BaseModel], handler: GetCoreSchemaHandler, /
    ) -> CoreSchema:
        return cls.pydantic_model.__get_pydantic_core_schema__(source, handler)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
        /,
    ) -> JsonSchemaValue:
        return cls.pydantic_model.__get_pydantic_json_schema__(core_schema, handler)

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
        mode: JsonSchemaMode = "validation",
    ) -> dict[str, Any]:
        return cls.pydantic_model.model_json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            schema_generator=schema_generator,
            mode=mode,
        )

    @classproperty
    def __pydantic_validator__(cls):
        return cls.pydantic_model.__pydantic_validator__

    @classproperty
    def model_fields(cls):
        return cls.pydantic_model.model_fields

    @classproperty
    def model_config(cls):
        return cls.pydantic_model.model_config


def get_validators_map(attrs: dict):
    return dict(
        filter(
            lambda x: isinstance(x[1], PydanticDescriptorProxy)
            and (
                isinstance(x[1].decorator_info, ModelValidatorDecoratorInfo)
                or isinstance(x[1].decorator_info, FieldValidatorDecoratorInfo)
            ),
            attrs.items(),
        )
    )


def get_serializer_map(attrs: dict):
    return dict(
        filter(
            lambda x: isinstance(x[1], PydanticDescriptorProxy)
            and isinstance(x[1].decorator_info, FieldSerializerDecoratorInfo),
            attrs.items(),
        )
    )


def datetime_field_serializer_factory(format: str):
    def datetime_field_serializer(self, value: Union[time, date, datetime], _info):
        if value is None:
            return value

        if isinstance(value, datetime):
            tz = pytz.timezone("Asia/Shanghai")
            value = value.astimezone(tz)
        return value.strftime(format) if value else value

    return datetime_field_serializer


def get_serializers_map_from_fields(fields_map: dict):
    serializers_map = {}
    for key, field in fields_map.items():
        if isinstance(field, DateTimeField) and (field_format := field.format):
            if key not in serializers_map:
                serializers_map[f"serializer_{key}"] = field_serializer(key)(
                    datetime_field_serializer_factory(field_format)
                )
    return serializers_map


class SerializerMetaclass(ABCMeta):
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        if raw_fields_map := dict(
            filter(
                lambda x: isinstance(x[1], TortoiseField)
                or isinstance(x[1], BaseModel)
                or (isinstance(x[1], type) and issubclass(x[1], BaseModel)),
                attrs.items(),
            )
        ):
            serializers_map = get_serializer_map(
                attrs
            ) | get_serializers_map_from_fields(raw_fields_map)

            fields_map = {}
            for key, field in raw_fields_map.items():
                if isinstance(field, TortoiseField):
                    fdesc = field.describe(serializable=False)

                    field_default = fdesc.get("default")
                    ptype = fdesc["python_type"]

                    if field_default is not None or fdesc.get("nullable"):
                        fields_map[key] = (
                            Optional[ptype],
                            Field(default=field.default),
                        )
                    else:
                        fields_map[key] = (ptype, Field(default=field.default))
                elif (
                    isinstance(field, type) and issubclass(field, BaseModel)
                ) or isinstance(field, BaseModel):
                    if not getattr(field, "required", False):
                        fields_map[key] = (
                            Optional[field],
                            Field(default=getattr(field, "default", None)),
                        )
                    else:
                        fields_map[key] = (field, Field())
                else:
                    raise NotImplementedError()

            validators_map = get_validators_map(attrs)

            if "model_config" in attrs:
                pconfig = attrs["model_config"]
            else:
                pconfig = PydanticModel.model_config.copy()

            if "title" not in pconfig:
                pconfig["title"] = name
            if "extra" not in pconfig:
                pconfig["extra"] = "forbid"

            pconfig["orig_model"] = None

            pydantic_model = create_model(
                name,
                model_config=pconfig,
                __validators__=validators_map | serializers_map,
                **fields_map,
            )
            return type(
                name, (SerializerModel,), attrs | {"pydantic_model": pydantic_model}
            )

        return super().__new__(mcs, name, bases, attrs)


class Serializer(BaseSerializer, metaclass=SerializerMetaclass):
    pydantic_model: BaseModel

    def __init__(self, *args, required=False, default=None, **kwargs):
        pass
