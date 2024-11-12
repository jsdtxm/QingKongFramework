from decimal import Decimal
from typing import Any

from libs.models.fields import data as models_data_fields

DEFAULT_CHAR_LENGTH = 4096


class DefaultDescribeMixin:
    default_value = None

    def describe(self, serializable: bool) -> dict:
        desc = super().describe(serializable)
        if desc["default"] is None:
            desc["default"] = self.default_value
        return desc


# Integer
class SmallIntegerField(models_data_fields.SmallIntegerField):
    default_value = 0


class IntegerField(DefaultDescribeMixin, models_data_fields.IntegerField):
    default_value = 0


class BigIntegerField(models_data_fields.BigIntegerField):
    default_value = 0


# Float
class FloatField(models_data_fields.FloatField):
    default_value = 0.0


class DecimalField(models_data_fields.DecimalField):
    default_value = Decimal("0.0")


# String
class CharField(models_data_fields.CharField):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", DEFAULT_CHAR_LENGTH)
        super().__init__(**kwargs)


class TextField(models_data_fields.TextField):
    pass


class EmailField(models_data_fields.EmailField):
    pass


# Time
class TimeField(models_data_fields.TimeField):
    pass


class DateField(models_data_fields.DateField):
    pass


class DateTimeField(models_data_fields.DateTimeField):
    pass


class TimeDeltaField(models_data_fields.TimeDeltaField):
    pass


# Others
class BooleanField(models_data_fields.BooleanField):
    pass


class BinaryField(models_data_fields.BinaryField):
    pass


class JSONField(models_data_fields.JSONField):
    pass


class UUIDField(models_data_fields.UUIDField):
    pass
