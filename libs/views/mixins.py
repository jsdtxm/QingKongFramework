from typing import TYPE_CHECKING

from starlette import status

from libs.responses import JSONResponse
from libs.serializers.model import ModelSerializer
from libs.models.base import BaseModel
from libs.requests import DjangoStyleRequest

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
            serializer = await self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = await self.get_serializer(queryset, many=True)
        return JSONResponse(serializer.model_dump())


class CreateModelMixin:
    """
    Create a model instance.
    """

    async def create(
        self: "CreateModelMixinType", request: DjangoStyleRequest, *args, **kwargs
    ):  # type: ignore
        serializer = await self.get_serializer(data=await request.data)
        await self.perform_create(serializer)
        return JSONResponse(
            serializer.model_dump(), status_code=status.HTTP_201_CREATED
        )

    async def perform_create(self, serializer: ModelSerializer):
        await serializer.save()


if TYPE_CHECKING:

    class CreateModelMixinType(CreateModelMixin, GenericViewSet):
        pass

