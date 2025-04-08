from starlette import status

from fastapp.contrib.auth.mixins import SuperUserRequiredMixin
from fastapp.contrib.auth.utils import CurrentUser
from fastapp.contrib.auth.views import GroupViewSet
from fastapp.contrib.dynamic_rbac.models import DynamicPermission
from fastapp.contrib.dynamic_rbac.serializers import (
    DynamicPermissionSerializer,
    PermIDsSerializer,
)
from fastapp.responses import JSONResponse
from fastapp.router import APIRouter
from fastapp.views import viewsets
from fastapp.views.decorators import action

dynamic_rbac_router = APIRouter(tags=["Dynamic RBAC"])


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


@dynamic_rbac_router.get("/permissions/")
async def user_permissions(user: CurrentUser):
    perms = await DynamicPermission.objects.filter(groups__user=user)

    serializer = viewsets.ListSerializerWrapper(
        [DynamicPermissionSerializer.model_validate(x) for x in perms]
    )

    return JSONResponse(serializer.model_dump())
