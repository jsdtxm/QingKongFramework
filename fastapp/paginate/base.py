from typing import Type

from pydantic import BaseModel, Field

from fastapp.responses import JSONResponse
from fastapp.utils.sql import get_limit_offset


class BaseFilter(BaseModel):
    page_size: int = Field(default=20)
    current: int = Field(default=1)


class BasePaginate:
    params_model: Type[BaseModel] = BaseFilter

    @classmethod
    async def paginate_queryset(cls, queryset, request, view):
        request_filter = cls.params_model(**request.GET.to_dict())
        limit, offset = get_limit_offset(
            request_filter.page_size, request_filter.current
        )
        total = await queryset.count()

        view.total = total

        return queryset.offset(offset).limit(limit)

    @classmethod
    def get_paginated_response(cls, data, total=None):
        return JSONResponse({"data": data, "total": total})
