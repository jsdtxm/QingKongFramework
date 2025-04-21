from collections.abc import Sequence
from typing import TYPE_CHECKING, Dict, Optional, Type

from pydantic import BaseModel, Field, create_model
from tortoise.fields.base import Field as TortoiseField
from tortoise.fields.relational import RelationalField

from fastapp.filters import filters
from fastapp.filters.filters import Filter, LookupExprEnum
from fastapp.models import QuerySet
from fastapp.models.fields import DecimalField, JSONField
from fastapp.requests import QueryParamsWrap


class FieldToFilter:
    _dict: Optional[dict] = None

    @classmethod
    def get(cls, field, default=None) -> Optional[Type[Filter]]:
        if cls._dict is None:
            cls._dict = {}
            for obj in filters.__dict__.values():
                if not (
                    isinstance(obj, type)
                    and issubclass(obj, Filter)
                    and obj is not Filter
                ):
                    continue
                related_field = next(
                    filter(lambda x: issubclass(x, TortoiseField), obj.__bases__), None
                )
                cls._dict[related_field] = obj
        return cls._dict.get(field, default)


def get_field_to_filter_kwargs(field):
    if isinstance(field, DecimalField):
        return {"max_digits": field.max_digits, "decimal_places": field.decimal_places}

    return {}


class FilterSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # 创建原始类
        new_class = super().__new__(cls, name, bases, attrs)

        # 收集继承的字段
        combined_attrs = {}
        for ancestor in reversed(new_class.__mro__):
            if filters := getattr(ancestor, "filters", None):
                combined_attrs |= filters

        if meta := attrs.get("Meta"):
            if model := getattr(meta, "model", None):
                fields_map = model._meta.fields_map

                fields = getattr(meta, "fields", None)
                exclude = getattr(meta, "exclude", [])

                non_related_fields_map = {
                    k: v
                    for k, v in fields_map.items()
                    if not isinstance(v, RelationalField)
                }

                field_filter_dict = {}
                if fields is None:
                    field_filter_dict = {
                        x: ["exact"] for x in set(non_related_fields_map.keys())
                    }
                elif isinstance(fields, list) or isinstance(fields, tuple):
                    field_filter_dict = {x: ["exact"] for x in set(fields)}
                elif isinstance(fields, dict):
                    field_filter_dict = {
                        k: (v if isinstance(v, list) or isinstance(v, tuple) else [v])
                        for k, v in fields.items()
                    }

                if exclude:
                    for field_name in exclude:
                        if field_name in field_filter_dict:
                            field_filter_dict.pop(field_name)

                # 构建新的类
                new_attrs = {k: v for k, v in attrs.items() if k.startswith("__")}
                for field_name in field_filter_dict:
                    if field_name not in non_related_fields_map:
                        raise ValueError(
                            f"Field '{field_name}' does not exist in model '{model.__name__}'"
                        )

                    field = non_related_fields_map[field_name]
                    filter_class = FieldToFilter.get(field.__class__)
                    if filter_class is None:
                        raise ValueError(
                            f"Field '{field_name}' does not support filtering"
                        )

                    kwargs = get_field_to_filter_kwargs(field)
                    if len(field_filter_dict[field_name]) <= 1:
                        new_attrs[field_name] = filter_class(
                            field_name=field_name,
                            **(
                                kwargs
                                | {"lookup_expr": field_filter_dict[field_name][0]}
                            ),
                        )
                    else:
                        for lookup_expr in field_filter_dict[field_name]:
                            if lookup_expr == LookupExprEnum.exact.value:
                                new_attrs[field_name] = filter_class(
                                    field_name=field_name,
                                    **kwargs,
                                )
                            else:
                                new_attrs[f"{field_name}__{lookup_expr}"] = (
                                    filter_class(
                                        field_name=field_name,
                                        **(kwargs | {"lookup_expr": lookup_expr}),
                                    )
                                )

                new_class = super().__new__(
                    cls, name, bases, new_attrs | combined_attrs
                )
                combined_attrs = new_attrs | combined_attrs

        # 获取所有声明的过滤器字段
        declared_filters: Dict[str, Filter] = {
            k: v for k, v in combined_attrs.items() if isinstance(v, Filter)
        }
        model_fields = {}

        for filter_name, filter_instance in declared_filters.items():
            # 获取字段的Python类型（如str、datetime）
            python_type = filter_instance.field_type

            # 将类型包装为Optional（字段可空）
            optional_type = Optional[python_type]

            # 创建Pydantic字段：类型为Optional，并设置别名
            model_fields[filter_name] = (
                optional_type,
                Field(default=None, alias=filter_instance.alias or None),
            )

        # 动态创建Pydantic模型并附加到类属性
        if model_fields:
            pydantic_model = create_model(
                f"{name}PydanticModel", __base__=BaseModel, **model_fields
            )
            new_class.PydanticModel = pydantic_model
        else:
            new_class.PydanticModel = None  # 无字段时设为None

        new_class.filters = declared_filters
        return new_class


class BaseFilterSet:
    if TYPE_CHECKING:
        filters: Dict[str, Filter]
        PydanticModel: Type[BaseModel]

    def __init__(self, data: QueryParamsWrap, queryset, *, request=None, **kwargs):
        self.data = data
        self.queryset = queryset
        self.request = request

        self.model_fields_map = queryset.model._meta.fields_map

    def filter_queryset(self, queryset):
        params = self.PydanticModel.model_validate(self.data.to_dict())

        for name, value in params.model_dump(exclude_unset=True).items():
            try:
                filter_obj = self.filters[name]
                if isinstance(
                    self.model_fields_map[filter_obj.source_field],
                    JSONField,
                ):
                    queryset = filter_obj.jsonfield_filter(queryset, value)
                else:
                    queryset = filter_obj.filter(queryset, value)

                assert isinstance(queryset, QuerySet), (
                    "Expected '%s.%s' to return a QuerySet, but got a %s instead."
                    % (
                        type(self).__name__,
                        name,
                        type(queryset).__name__,
                    )
                )
            except KeyError:
                pass
        return queryset

    @property
    def qs(self):
        if not hasattr(self, "_qs"):
            self._qs = self.filter_queryset(self.queryset.all())
        return self._qs


# FIXME 不支持继承
class FilterSet(BaseFilterSet, metaclass=FilterSetMetaclass):
    pass
