import datetime
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)
from uuid import UUID

from pydantic import constr
from tortoise.fields.base import Field

from fastapp.models.fields import data as models_data_fields

DEFAULT_CHAR_LENGTH = 4096

VALUE = TypeVar("VALUE")


class LookupExprEnum(Enum):
    exact = "exact"  # 精确匹配
    iexact = "iexact"  # 忽略大小写的精确匹配
    contains = "contains"  # 包含
    icontains = "icontains"  # 忽略大小写的包含
    in_ = "in"  # 在给定的列表中
    gt = "gt"  # 大于
    gte = "gte"  # 大于等于
    lt = "lt"  # 小于
    lte = "lte"  # 小于等于
    startswith = "startswith"  # 以...开始
    istartswith = "istartswith"  # 忽略大小写的以...开始
    endswith = "endswith"  # 以...结束
    iendswith = "iendswith"  # 忽略大小写的以...结束
    range = "range"  # 范围内
    isnull = "isnull"  # 是否为null
    regex = "regex"  # 正则表达式匹配
    iregex = "iregex"  # 忽略大小写的正则表达式匹配

    # 日期
    date = "date"
    year = "year"
    month = "month"
    day = "day"
    hour = "hour"
    minute = "minute"
    second = "second"

    # PostgreSQL 特有的查询表达式
    contained_by = "contained_by"  # 被包含于
    overlap = "overlap"  # 重叠
    has_key = "has_key"  # 具有键
    has_keys = "has_keys"  # 具有所有指定的键
    has_any_keys = "has_any_keys"  # 具有任意一个指定的键
    trigram_similar = "trigram_similar"  # 三元相似度搜索


LookupExprEnumValues = {item.value for item in LookupExprEnum}


class Filter(Generic[VALUE]):
    def __init__(
        self,
        field_name=None,
        lookup_expr: str = None,
        *,
        alias=None,
        label=None,
        method=None,
        distinct=False,
        exclude=False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if lookup_expr is None:
            lookup_expr = LookupExprEnum.exact.value
        if lookup_expr not in LookupExprEnumValues:
            raise ValueError(f"Invalid lookup_expr: {lookup_expr}")

        self.field_name = field_name
        self.lookup_expr = lookup_expr

        self.alias = alias
        self.label = label
        self.method = method
        self.distinct = distinct
        self.exclude = exclude

        self.extra = kwargs
        self.extra.setdefault("required", False)

        fields = self.field_name.split("__", 1)
        self.source_field = fields[0]
        self.nested_field = fields[1] if len(fields) > 1 else None

    def filter(self, queryset, value):
        lookup_expr = (
            "" if self.lookup_expr == LookupExprEnum.exact.value else self.lookup_expr
        )

        return queryset.filter(
            **{f"{self.field_name}{f'__{lookup_expr}' if lookup_expr else ''}": value}
        )

    def jsonfield_filter(self, queryset, value):
        if self.lookup_expr == LookupExprEnum.contains.value:
            return queryset.filter(
                **{f"{self.source_field}__contains": {self.nested_field: value}}
            )

        lookup_expr = (
            "" if self.lookup_expr == LookupExprEnum.exact.value else self.lookup_expr
        )

        return queryset.filter(
            **{
                f"{self.source_field}__filter": {
                    f"{self.nested_field}{f'__{lookup_expr}' if lookup_expr else ''}": value
                }
            }
        )


# Integer
class SmallIntegerFilter(Filter[int], models_data_fields.SmallIntegerField):
    default_value = 0


class IntegerFilter(Filter[int], models_data_fields.IntegerField):
    default_value = 0


class BigIntegerFilter(Filter[int], models_data_fields.BigIntegerField):
    default_value = 0


# Float
class FloatFilter(Filter[float], models_data_fields.FloatField):
    default_value = 0.0


class DecimalFilter(Filter[Decimal], models_data_fields.DecimalField):
    default_value = Decimal("0.0")


# String
class CharFilter(Filter[str], models_data_fields.CharField):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", DEFAULT_CHAR_LENGTH)
        super().__init__(**kwargs)

    @property
    def pydantic_type(self):
        return constr(max_length=self.max_length)


class TextFilter(Filter[str], models_data_fields.TextField):
    pass


class EmailFilter(Filter[str], models_data_fields.EmailField):
    pass


# Time
class DateTimeFormatMixin:
    def __init__(self, format: Optional[str] = None, **kwargs: Any) -> None:
        self.format = format
        super().__init__(**kwargs)


class TimeFilter(
    DateTimeFormatMixin, Filter[datetime.time], models_data_fields.TimeField
):
    pass


class DateFilter(
    DateTimeFormatMixin, Filter[datetime.date], models_data_fields.DateField
):
    pass


class DateTimeFilter(
    DateTimeFormatMixin,
    Filter[datetime.datetime],
    models_data_fields.DateTimeField,
):
    pass


class TimeDeltaFilter(Filter[datetime.timedelta], models_data_fields.TimeDeltaField):
    pass


# Others
class BooleanFilter(Filter[bool], models_data_fields.BooleanField):
    pass


class BinaryFilter(Filter[bytes], models_data_fields.BinaryField):
    pass


class JSONFilter(Filter[Union[dict, list]], models_data_fields.JSONField):
    pass


class UUIDFilter(Filter[UUID], models_data_fields.UUIDField):
    pass


# Serializer Only
class NestedFilter(Field):
    pass


class ListSerializer(Filter[list], NestedFilter, list):
    def __init__(self, child, **kwargs: Any):
        super().__init__(**({"default": []} | kwargs))
        self.child = child
        if isinstance(child, Field):
            child_desc = child.describe(serializable=False)
            child_type = child_desc["python_type"]
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
