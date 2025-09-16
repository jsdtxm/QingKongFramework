from typing import TYPE_CHECKING, Dict, Optional, Type

from pydantic import BaseModel, Field, create_model
from tortoise.fields.base import Field as TortoiseField
from tortoise.fields.relational import RelationalField

from fastapp.filters import filters
from fastapp.filters.filters import (
    BigIntegerFilter,
    Filter,
    ListFilter,
    LookupExprEnum,
    OrderingFilter,
)
from fastapp.models import BaseModel as FastappBaseModel
from fastapp.models import QuerySet
from fastapp.models.fields import DecimalField, JSONField
from fastapp.models.fields.data import PositiveIntegerField, PositiveSmallIntegerField
from fastapp.requests import QueryParamsWrap

try:
    from fastapp.models.fields.vector import VectorField
except ImportError:
    VectorField = None


class FieldToFilter:
    _dict: Optional[dict] = None

    @classmethod
    def get(cls, field, default=None) -> Optional[Type[Filter]]:
        if cls._dict is None:
            cls._dict = {
                PositiveIntegerField: filters.IntegerFilter,
                PositiveSmallIntegerField: filters.SmallIntegerFilter,
            }
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
        combined_filters = {}
        combined_filter_sets = {}
        for ancestor in reversed(new_class.__mro__[1:]):
            if ancestor_filters := getattr(ancestor, "filters", None):
                combined_filters |= ancestor_filters
            for attr_name, attr_value in ancestor.__dict__.items():
                if isinstance(attr_value, BaseFilterSet):
                    combined_filter_sets[attr_name] = attr_value

        self_declared_filters: Dict[str, Filter] = {
            k: v for k, v in attrs.items() if isinstance(v, Filter)
        }
        if self_declared_filters:
            combined_filters |= self_declared_filters

        # 嵌套的BaseFilterSet
        self_declared_filter_sets = {
            k: v for k, v in attrs.items() if isinstance(v, BaseFilterSet)
        }
        combined_filter_sets |= self_declared_filter_sets

        # combined_filter_sets
        for k, v in combined_filter_sets.items():
            for attr, nested_filter in v.filters.items():
                if nested_filter.__class__ is OrderingFilter:
                    continue
                combined_filters[f"{k}__{attr}"] = nested_filter.__class__(
                    **(
                        nested_filter.__dict__
                        | {"field_name": f"{k}__{nested_filter.field_name}"}
                    )
                )

        if meta := attrs.get("Meta"):
            if model := getattr(meta, "model", None):
                fields_map = model._meta.fields_map
                m2m_fields = model._meta.m2m_fields

                fields = getattr(meta, "fields", None)
                exclude = getattr(meta, "exclude", [])

                non_related_fields_map = {
                    k: v
                    for k, v in fields_map.items()
                    if not isinstance(v, RelationalField)
                }

                field_filter_dict = {
                    x: ["exact"] for x in set(non_related_fields_map.keys())
                }
                if isinstance(fields, list) or isinstance(fields, tuple):
                    field_filter_dict |= {x: ["exact"] for x in set(fields)}
                elif isinstance(fields, dict):
                    field_filter_dict |= {
                        k: (v if isinstance(v, list) or isinstance(v, tuple) else [v])
                        for k, v in fields.items()
                    }

                if exclude:
                    for field_name in exclude:
                        if field_name in field_filter_dict:
                            field_filter_dict.pop(field_name)

                # 构建新的类
                order_fields = [("id", "id")]
                new_attrs = {k: v for k, v in attrs.items() if k.startswith("__")}
                for field_name, field in field_filter_dict.items():
                    if field_name not in non_related_fields_map:
                        raise ValueError(
                            f"Field '{field_name}' does not exist in model '{model.__name__}'"
                        )

                    order_fields.append((field_name, field_name))

                    field = non_related_fields_map[field_name]
                    kwargs = get_field_to_filter_kwargs(field)

                    for lookup_expr in field_filter_dict[field_name]:
                        new_attr_name = (
                            field_name
                            if lookup_expr == LookupExprEnum.exact.value
                            or len(field_filter_dict[field_name]) == 1
                            else f"{field_name}__{lookup_expr}"
                        )

                        # HACK ignore VectorField
                        if VectorField and isinstance(field, VectorField):
                            continue

                        filter_class = FieldToFilter.get(field.__class__)
                        if filter_class is None:
                            raise ValueError(
                                f"Field '{field_name}' does not support filtering"
                            )

                        if lookup_expr == LookupExprEnum.in_.value:
                            kwargs |= {"child": filter_class()}
                            filter_class = ListFilter

                        new_attrs[new_attr_name] = filter_class(
                            field_name=field_name,
                            **(kwargs | {"lookup_expr": lookup_expr}),
                        )

                    if m2m_fields:
                        for field_name in m2m_fields:
                            # TODO Non ID association is not supported yet
                            new_attrs[f"{field_name}_id"] = BigIntegerFilter(
                                field_name=field_name,
                            )

                new_attrs["o"] = OrderingFilter(fields=order_fields)

                new_class = super().__new__(
                    cls, name, bases, new_attrs | combined_filters
                )
                combined_filters = new_attrs | combined_filters

        # 获取所有声明的过滤器字段
        declared_filters: Dict[str, Filter] = {
            k: v for k, v in combined_filters.items() if isinstance(v, Filter)
        }
        model_fields = {}

        for filter_name, filter_instance in declared_filters.items():
            # 获取字段的Python类型（如str、datetime）
            python_type = filter_instance.field_type

            # 将类型包装为Optional（字段可空）
            optional_type = Optional[python_type]

            # TODO 或许可以支持一下字段以及模型校验
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

    def __init__(
        self,
        data: Optional[QueryParamsWrap] = None,
        queryset=None,
        *,
        request=None,
        **kwargs,
    ):
        self.queryset = queryset
        self.request = request

        self.data = data or request.GET

        self._params = None

        if self.queryset:
            self.model_fields_map = self.get_model_fields_map(self.queryset)
        else:
            self.model_fields_map = None

    def get_model_fields_map(self, queryset):
        if (
            isinstance(queryset, type) and issubclass(queryset, FastappBaseModel)
        ) or isinstance(queryset, FastappBaseModel):
            model_fields_map = queryset._meta.fields_map
        else:
            model_fields_map = queryset.model._meta.fields_map

        return model_fields_map

    @property
    def params(self):
        if self._params is None:
            data = self.data
            if not isinstance(data, dict):
                data = data.to_dict()
            self._params = self.PydanticModel.model_validate(data)

        return self._params

    def filter_queryset(self, queryset):
        if self.model_fields_map is None:
            self.model_fields_map = self.get_model_fields_map(queryset)

        params = self.params.model_dump(exclude_unset=True)
        ordering_filters = []
        for name, value in params.items():
            try:
                filter_obj = self.filters[name]
                if isinstance(filter_obj, OrderingFilter):
                    ordering_filters.append((name, value, filter_obj))
                    continue

                model_field = self.model_fields_map[filter_obj.source_field]

                if isinstance(model_field, JSONField):
                    queryset = filter_obj.jsonfield_filter(queryset, value)
                else:
                    queryset = filter_obj.filter(
                        queryset,
                        value,
                        model_field
                        if isinstance(model_field, RelationalField)
                        else None,
                    )

                assert isinstance(queryset, QuerySet), (
                    "Expected '%s.%s' to return a QuerySet, but got a %s instead."
                    % (
                        type(self).__name__,
                        name,
                        type(queryset).__name__,
                    )
                )
            except KeyError as e:
                print("[Filter ERROR]", e)

        if ordering_filters:
            for name, value, filter_obj in ordering_filters:
                # TODO 支持多重排序
                if value.replace("-", "") not in filter_obj.allow_order_fields:
                    raise ValueError(f"Invalid value `{value}` for ordering")
                queryset = queryset.order_by(value)

        return queryset.distinct()

    @property
    def qs(self):
        if not hasattr(self, "_qs"):
            self._qs = self.filter_queryset(self.queryset.all())
        return self._qs


# FIXME 不支持继承
class FilterSet(BaseFilterSet, metaclass=FilterSetMetaclass):
    pass
