from pydantic import BaseModel, Field

from fastapp.responses import JSONResponse
from fastapp.utils.sql import get_limit_offset


class ProTableFilter(BaseModel):
    page_size: int = Field(default=20, alias="pageSize")
    current: int = Field(default=1)


class ProPaginateMixin:
    async def paginate_queryset(self, queryset):
        try:
            request_filter = ProTableFilter(**self.request.GET.to_dict())
            limit, offset = get_limit_offset(
                request_filter.page_size, request_filter.current
            )
            self.total = await queryset.count()
            return queryset.offset(offset).limit(limit)

        except Exception:
            return None

    def get_paginated_response(self, data):
        return JSONResponse({"data": data, "total": self.total, "success": True})
