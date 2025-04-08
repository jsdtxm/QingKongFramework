from starlette import status

from libs.contrib.auth.mixins import SuperUserRequiredMixin
from libs.contrib.auth.views import GroupViewSet
from libs.contrib.dynamic_rbac.models import DynamicPermission
from libs.contrib.dynamic_rbac.serializers import (
    DynamicPermissionSerializer,
    PermIDsSerializer,
)
from libs.responses import JSONResponse
from libs.views import viewsets
from libs.views.decorators import action


class DynamicPermissionViewSet(SuperUserRequiredMixin, viewsets.ReadOnlyModelViewSet):
    queryset = DynamicPermission
    serializer_class = DynamicPermissionSerializer


class GroupWithDynamicPermissionViewSet(GroupViewSet):
    @action(detail=True, methods=["get"], url_path="dynamic_permission")
    async def list_dynamic_permission(self, request, id=None):
        group = await self.get_object()
        dynamic_permissions = await group.dynamic_permissions.all()

        serializer = viewsets.ListSerializerWrapper(
            [DynamicPermissionSerializer.model_validate(x) for x in dynamic_permissions]
        )

        return JSONResponse(serializer.model_dump())

    @action(detail=True, methods=["post"], url_path="dynamic_permission")
    async def add_dynamic_permission(self, request, id=None):
        group = await self.get_object()

        serializer = PermIDsSerializer.model_validate(await request.data)
        dynamic_permissions = await DynamicPermission.objects.filter(
            id__in=serializer.perm_ids
        )
        await group.dynamic_permissions.add(*dynamic_permissions)
        return JSONResponse(
            {
                "msg": "ok",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path="dynamic_permission")
    async def remove_dynamic_permission(self, request, id=None):
        group = await self.get_object()

        serializer = PermIDsSerializer.model_validate(await request.data)

        dynamic_permissions = await DynamicPermission.objects.filter(
            id__in=serializer.perm_ids
        )
        await group.dynamic_permissions.remove(*dynamic_permissions)
        return JSONResponse(
            {
                "msg": "ok",
            },
            status=status.HTTP_200_OK,
        )
