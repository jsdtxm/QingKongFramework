from typing import TYPE_CHECKING, Dict, Optional, Type

from pydantic import BaseModel, Field, create_model

from fastapp.filters.filters import Filter
from fastapp.models import QuerySet
from fastapp.models.fields import JSONField
from fastapp.requests import QueryParamsWrap


class FilterSetMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # 创建原始类
        new_class = super().__new__(cls, name, bases, attrs)

        # 获取所有声明的过滤器字段
        declared_filters: Dict[str, Filter] = {
            k: v for k, v in attrs.items() if isinstance(v, Filter)
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


class FilterSet(BaseFilterSet, metaclass=FilterSetMetaclass):
    pass
