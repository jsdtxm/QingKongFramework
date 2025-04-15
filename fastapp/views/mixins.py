from typing import TYPE_CHECKING

from starlette import status

from fastapp.models.base import BaseModel
from fastapp.requests import DjangoStyleRequest
from fastapp.responses import JSONResponse
from fastapp.serializers.model import ModelSerializer

if TYPE_CHECKING:
    from fastapp.views.viewsets import GenericViewSet


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
        queryset = await self.filter_queryset(self.get_queryset())

        page = await self.paginate_queryset(queryset)
        if page is not None:
            serializer = await self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.model_dump())

        serializer = await self.get_serializer(queryset, many=True)
        return JSONResponse(serializer.model_dump())


class CreateModelMixin:
    """
    Create a model instance.
    """

    async def create(  # type: ignore
        self: "CreateModelMixinType", request: DjangoStyleRequest, *args, **kwargs
    ):
        serializer = await self.get_serializer(data=await request.data)
        instance = await self.perform_create(serializer)  # type: ignore

        return JSONResponse(
            (
                await self.get_serializer(instance, override_action="retrieve")
            ).model_dump(),
            status_code=status.HTTP_201_CREATED,
        )

    async def perform_create(self, serializer: ModelSerializer):
        return await serializer.save()


if TYPE_CHECKING:

    class CreateModelMixinType(CreateModelMixin, GenericViewSet):
        pass


class UpdateModelMixin:
    """
    Update a model instance.
    """

    async def update(  # type: ignore
        self: "UpdateModelMixinType", request: DjangoStyleRequest, *args, **kwargs
    ):
        instance = await self.get_object()
        serializer = await self.get_serializer(instance, data=await request.data)

        await self.perform_update(serializer)

        return JSONResponse(
            (
                await self.get_serializer(serializer._instance, override_action="retrieve")
            ).model_dump(),
            status_code=status.HTTP_200_OK,
        )

    async def perform_update(self, serializer: ModelSerializer):
        await serializer.save()


if TYPE_CHECKING:

    class UpdateModelMixinType(UpdateModelMixin, GenericViewSet):
        pass


class DestroyModelMixin:
    """
    Destroy a model instance.
    """

    async def destroy(self: "DestroyModelMixinType", request, *args, **kwargs):  # type: ignore
        instance = await self.get_object()
        await self.perform_destroy(instance)
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    async def perform_destroy(self, instance: BaseModel):
        await instance.delete()


if TYPE_CHECKING:

    class DestroyModelMixinType(DestroyModelMixin, GenericViewSet):
        pass
