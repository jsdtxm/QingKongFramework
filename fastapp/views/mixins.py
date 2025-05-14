from typing import TYPE_CHECKING

from starlette import status

from fastapp.models.base import BaseModel, QuerySet
from fastapp.models.fields import DateField, DateTimeField, RelationalField
from fastapp.requests import DjangoStyleRequest
from fastapp.responses import JSONResponse
from fastapp.serializers.model import ModelSerializer
from fastapp.views.decorators import action

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

    async def list(self: "GenericViewSet", request, *args, **kwargs) -> QuerySet:  # type: ignore
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
                await self.get_serializer(
                    serializer._instance, override_action="retrieve"
                )
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


class ModelFieldsOperatorMixin:
    def get_fields_map(  # type: ignore[misc]
        self: "ModelFieldsOperatorMixinType",
        include_backward: bool = False,
        include_m2m: bool = True,
        include_auto: bool = True,
        include_fk_id: bool = True,
    ):
        model = self.get_queryset().model

        fields_map = model._meta.fields_map

        if not include_backward:
            field_set = model._meta.backward_fk_fields | model._meta.backward_o2o_fields

            fields_map = {k: v for k, v in fields_map.items() if k not in field_set}

        if not include_m2m:
            fields_map = {
                k: v for k, v in fields_map.items() if k not in model._meta.m2m_fields
            }

        if not include_auto:
            fields_map = {
                k: v
                for k, v in fields_map.items()
                if not v.generated
                and not (
                    (isinstance(v, DateTimeField) or isinstance(v, DateField))
                    and (v.auto_now or v.auto_now_add)
                )
            }

        if not include_fk_id:
            fk_id_field_set = {f"{x}_id" for x in model._meta.fk_fields}
            fields_map = {
                k: v for k, v in fields_map.items() if k not in fk_id_field_set
            }

        return fields_map

    def get_verbose_name_dict(self):  # type: ignore[misc]
        res = {}
        for k, v in ModelFieldsOperatorMixin.get_fields_map(self).items():
            verbose_name = getattr(v, "verbose_name", k)
            if verbose_name and verbose_name != k:
                res[k] = verbose_name
            if isinstance(v, RelationalField):
                if verbose_name:
                    res[f"{k}_id"] = f"{verbose_name}ID"
                for sk, sv in v.related_model._meta.fields_map.items():
                    if sub_verbose_name := getattr(sv, "verbose_name", None):
                        res[f"{k}.{sk}"] = f"{verbose_name}.{sub_verbose_name}"
                    elif verbose_name:
                        res[f"{k}.{sk}"] = f"{verbose_name}.{sk}"

        return res


if TYPE_CHECKING:

    class ModelFieldsOperatorMixinType(ModelFieldsOperatorMixin, GenericViewSet):
        pass


class ModelSchemaMixin:
    @action(detail=False, methods=["get"])
    async def schema(self: "ModelSchemaMixinType", request: DjangoStyleRequest):  # type: ignore[misc]
        serializer_class = self.get_serializer_class()
        fields_map = serializer_class.field_map()
        verbose_name_dict = ModelFieldsOperatorMixin.get_verbose_name_dict(self)

        res = []
        for field_name, field in fields_map.items():
            item = {
                "field_name": field_name,
                "verbose_name": verbose_name_dict.get(field_name),
                "required": not field.get("nullable"),
            }
            if choices := field.get("choices", None):
                item["choices"] = [
                    {"value": choice.value, "label": choice.label}
                    for choice in choices.choices
                ]

            res.append(item)

        return res


if TYPE_CHECKING:

    class ModelSchemaMixinType(
        ModelSchemaMixin, ModelFieldsOperatorMixin, GenericViewSet
    ):
        pass
