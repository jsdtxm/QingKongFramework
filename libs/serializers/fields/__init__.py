import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Generic, List, Type, TypeVar, Union, overload
from uuid import UUID

from pydantic import constr
from tortoise.fields import Field

from libs.models.fields import data as models_data_fields

if TYPE_CHECKING:  # pragma: nocoverage
    from libs.serializers.base import Serializer

T = TypeVar("T")
DEFAULT_CHAR_LENGTH = 4096


class SerializerMixin(Generic[T]):
    default_value = None

    def describe(self, serializable: bool) -> dict:
        desc = super().describe(serializable)
        if desc["default"] is None:
            desc["default"] = self.default_value
        return desc

    if TYPE_CHECKING:

        def __new__(cls, *args: Any, **kwargs: Any) -> T: ...

        @overload
        def __get__(self, instance: "Serializer", owner: Type["Serializer"]) -> T: ...


# Integer
class SmallIntegerField(SerializerMixin[int], models_data_fields.SmallIntegerField):
    default_value = 0


class IntegerField(SerializerMixin[int], models_data_fields.IntegerField):
    default_value = 0


class BigIntegerField(SerializerMixin[int], models_data_fields.BigIntegerField):
    default_value = 0


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
class TimeField(SerializerMixin[datetime.time], models_data_fields.TimeField):
    pass


class DateField(SerializerMixin[datetime.date], models_data_fields.DateField):
    pass


class DateTimeField(
    SerializerMixin[datetime.datetime], models_data_fields.DateTimeField
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


class JSONField(SerializerMixin[Union[dict, list]], models_data_fields.JSONField):
    pass


class UUIDField(SerializerMixin[UUID], models_data_fields.UUIDField):
    pass


# Serializer Only
class NestedField(Field):
    pass


class ListSerializer(SerializerMixin[list], NestedField, list):
    def __init__(self, child, **kwargs: Any):
        super().__init__(**({'default': []}|kwargs))
        self.child = child
        if isinstance(child, Field):
            child_desc = child.describe(serializable=False)
            child_type = child_desc['python_type']
            self.field_type = list[child_type]
        else:
            self.field_type = list[type(child)]

    def describe(self, serializable: bool) -> dict:
        desc = super().describe(serializable)
        desc["child"] = self.child
        desc["pydantic_type"] = self.pydantic_type
        return desc

    @property
    def pydantic_type(self):
        return List

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(child={self.child})"
