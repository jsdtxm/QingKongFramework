from typing import TYPE_CHECKING

from libs.responses import JSONResponse

if TYPE_CHECKING:
    from libs.views.viewsets import GenericViewSet


class RetrieveModelMixin:
    """
    Retrieve a model instance.
    """

    async def retrieve(self: "GenericViewSet", request, *args, **kwargs):  # type: ignore
        instance = await self.get_object()
        serializer = await self.get_serializer(instance)
        return JSONResponse(serializer.model_dump())


class ListModelMixin:
    """
    List a queryset.
    """

    async def list(self: "GenericViewSet", request, *args, **kwargs):  # type: ignore
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = await self.get_serializer(queryset, many=True)
        return JSONResponse(serializer.model_dump())
