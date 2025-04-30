from starlette import status

from fastapp.contrib.auth.mixins import SuperUserRequiredMixin
from fastapp.contrib.auth.utils import CurrentUser
from fastapp.contrib.auth.views import AdminGroupViewSet
from fastapp.contrib.dynamic_rbac.filters import DynamicPermissionFilterSet
from fastapp.contrib.dynamic_rbac.models import DynamicPermission
from fastapp.contrib.dynamic_rbac.serializers import (
    DynamicPermissionSerializer,
    PermIDsSerializer,
)
from fastapp.filters import FilterBackend
from fastapp.responses import JSONResponse
from fastapp.router import APIRouter
from fastapp.views import viewsets
from fastapp.views.decorators import action

dynamic_rbac_router = APIRouter(tags=["Dynamic RBAC"])


class DynamicPermissionViewSet(SuperUserRequiredMixin, viewsets.ReadOnlyModelViewSet):
    """
    A viewset that provides 'list' and 'retrieve' actions for DynamicPermission instances.
    Only superusers are allowed to access the views provided by this viewset.
    """

    queryset = DynamicPermission
    serializer_class = DynamicPermissionSerializer
    filter_backends = [FilterBackend]
    filterset_class = DynamicPermissionFilterSet


class AdminGroupWithDynamicPermissionViewSet(AdminGroupViewSet):
    """
    A viewset that extends `AdminGroupViewSet` to handle admin groups with dynamic permissions.
    It inherits all the functionalities from `AdminGroupViewSet` and can be used to add
    custom actions related to dynamic permissions management for admin groups.
    """

    @action(detail=True, methods=["get"], url_path="dynamic_permission")
    async def list_dynamic_permission(self, request, id=None):
        """
        List all dynamic permissions associated with a specific admin group.

        Args:
            request (Request): The incoming HTTP request.
            id (Optional[int]): The ID of the admin group. Defaults to None.

        Returns:
            JSONResponse: A JSON response containing the list of dynamic permissions.
        """
        group = await self.get_object()
        dynamic_permissions = await group.dynamic_permissions.all()

        serializer = viewsets.ListSerializerWrapper(
            [DynamicPermissionSerializer.model_validate(x) for x in dynamic_permissions]
        )

        return JSONResponse(serializer.model_dump())

    @action(detail=True, methods=["post"], url_path="dynamic_permission")
    async def add_dynamic_permission(self, request, id=None):
        """
        Add specific dynamic permissions to a specific admin group.

        Args:
            request (Request): The incoming HTTP request.
            id (Optional[int]): The ID of the admin group. Defaults to None.

        Returns:
            JSONResponse: A JSON response indicating the operation was successful.
        """
        group = await self.get_object()

        serializer = PermIDsSerializer.model_validate(await request.data)
        dynamic_permissions = await DynamicPermission.objects.filter(
            id__in=serializer.perm_ids
        )
        await group.dynamic_permissions.add(*dynamic_permissions)
        return JSONResponse(
            {
                "message": "ok",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["delete"], url_path="dynamic_permission")
    async def remove_dynamic_permission(self, request, id=None):
        """
        Remove specific dynamic permissions from a specific admin group.

        Args:
            request (Request): The incoming HTTP request.
            id (Optional[int]): The ID of the admin group. Defaults to None.

        Returns:
            JSONResponse: A JSON response indicating the operation was successful.
        """
        group = await self.get_object()

        serializer = PermIDsSerializer.model_validate(await request.data)

        dynamic_permissions = await DynamicPermission.objects.filter(
            id__in=serializer.perm_ids
        )
        await group.dynamic_permissions.remove(*dynamic_permissions)
        return JSONResponse(
            {
                "message": "ok",
            },
            status=status.HTTP_200_OK,
        )


@dynamic_rbac_router.get("/permissions/")
async def user_permissions(user: CurrentUser):
    """
    Retrieve all dynamic permissions associated with a specific user.

    Args:
        user (CurrentUser): The current user instance.

    Returns:
        JSONResponse: A JSON response containing the list of dynamic permissions.
    """
    perms = await DynamicPermission.objects.filter(groups__user_set=user)

    serializer = viewsets.ListSerializerWrapper(
        [DynamicPermissionSerializer.model_validate(x) for x in perms]
    )

    return JSONResponse(serializer.model_dump())
