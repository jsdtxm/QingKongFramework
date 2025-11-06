import datetime
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)
from uuid import UUID

from pydantic import constr
from tortoise.fields.base import Field as RawField

from fastapp.models.fields import data as models_data_fields

if TYPE_CHECKING:  # pragma: nocoverage
    from fastapp.serializers.base import Serializer
    from fastapp.serializers.model import ModelSerializer


DEFAULT_CHAR_LENGTH = 4096

VALUE = TypeVar("VALUE")


if TYPE_CHECKING:

    class Field(RawField[VALUE]):
        @overload
        def __get__(
            self, instance: "Serializer", owner: Type["Serializer"]
        ) -> VALUE: ...
else:
    Field = RawField

class SerializerMixin(Generic[VALUE]):
    default_value = None

    def describe(self, serializable: bool) -> dict:
        desc = super().describe(serializable)
        if desc["default"] is None:
            desc["default"] = self.default_value
        return desc

    if TYPE_CHECKING:

        def __new__(cls, *args: Any, **kwargs: Any) -> "Field[VALUE]":
            return super().__new__(cls)

        @overload
        def __get__(
            self, instance: None, owner: Type["Serializer"]
        ) -> "Field[VALUE]": ...

        @overload
        def __get__(
            self, instance: "Serializer", owner: Type["Serializer"]
        ) -> VALUE: ...

        @overload
        def __get__(
            self, instance: "ModelSerializer", owner: Type["ModelSerializer"]
        ) -> VALUE: ...

        def __get__(
            self, instance: Optional["Serializer"], owner: Type["Serializer"]
        ) -> "Field[VALUE] | VALUE": ...

        @overload
        def __set__(self, instance: "ModelSerializer", value: VALUE) -> None: ...

        def __set__(self, instance: "Serializer", value: VALUE) -> None: ...


# Integer
class SmallIntegerField(SerializerMixin[int], models_data_fields.SmallIntegerField):
    default_value = 0


class IntegerField(SerializerMixin[int], models_data_fields.IntegerField):
    default_value = 0


class BigIntegerField(SerializerMixin[int], models_data_fields.BigIntegerField):
    default_value = 0

# TODO 添加PositiveIntegerField

# Float
class FloatField(SerializerMixin[float], models_data_fields.FloatField):
    default_value = 0.0


class DecimalField(SerializerMixin[Decimal], models_data_fields.DecimalField):
    default_value = Decimal("0.0")


# String
class CharField(SerializerMixin[str], models_data_fields.CharField):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", DEFAULT_CHAR_LENGTH)
        super().__init__(**kwargs)

    @property
    def pydantic_type(self):
        return constr(max_length=self.max_length)


class TextField(SerializerMixin[str], models_data_fields.TextField):
    pass


class EmailField(SerializerMixin[str], models_data_fields.EmailField):
    pass


# Time
class DateTimeFormatMixin:
    def __init__(self, format: Optional[str] = None, **kwargs: Any) -> None:
        self.format = format
        super().__init__(**kwargs)


class TimeField(
    DateTimeFormatMixin, SerializerMixin[datetime.time], models_data_fields.TimeField
):
    pass


class DateField(
    DateTimeFormatMixin, SerializerMixin[datetime.date], models_data_fields.DateField
):
    pass


class DateTimeField(
    DateTimeFormatMixin,
    SerializerMixin[datetime.datetime],
    models_data_fields.DateTimeField,
):
    pass


class TimeDeltaField(
    SerializerMixin[datetime.timedelta], models_data_fields.TimeDeltaField
):
    pass


# Others
class BooleanField(SerializerMixin[bool], models_data_fields.BooleanField):
    pass


class BinaryField(SerializerMixin[bytes], models_data_fields.BinaryField):
    pass


JsonFieldType = TypeVar("JsonFieldType")


class JSONField(SerializerMixin[JsonFieldType], models_data_fields.JSONField):
    pass


class UUIDField(SerializerMixin[UUID], models_data_fields.UUIDField):
    pass


# Serializer Only
class NestedField(Field):
    pass


class ListSerializer(SerializerMixin[list], NestedField, list):  # type: ignore[misc]
    def __init__(
        self,
        child,
        allow_primary_key: bool = False,
        writable: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**({"default": []} | kwargs))
        self.child = child
        self.allow_primary_key = allow_primary_key
        self.writable = writable

        if isinstance(child, Field):
            child_desc = child.describe(serializable=False)
            child_type = child_desc["python_type"]
            self.field_type = list[child_type]
        else:
            self.field_type = list[type(child)]

    def describe(self, serializable: bool) -> dict:
        desc = super().describe(serializable)
        desc["nested_field"] = True
        desc["child"] = self.child
        desc["pydantic_type"] = self.pydantic_type
        desc["allow_primary_key"] = self.allow_primary_key
        desc["writable"] = self.writable

        return desc

    @property
    def pydantic_type(self):
        return List

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(child={self.child})"


ListField = ListSerializer


class ExtendJsonField(
    Field[Union[dict, list, int, float, bool, str]], dict, list, int, float, bool, str
):
    default_value = None
