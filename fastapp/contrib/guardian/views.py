from collections import defaultdict

from starlette import status

from fastapp import serializers
from fastapp.contrib.auth import get_user_model
from fastapp.contrib.auth.serializers import UserSerializer
from fastapp.contrib.contenttypes.models import ContentType
from fastapp.contrib.guardian.serializers import PermActionSerializer
from fastapp.contrib.guardian.shortcuts import (
    assign_perm,
    get_user_obj_perms_model_class,
    remove_perm,
)
from fastapp.responses import JSONResponse
from fastapp.views.decorators import action

User = get_user_model()


class ObjectPermissionActionMixin:
    """
    Mixin for object permission actions.
    """

    user_serializer: type[serializers.BaseSerializer] = UserSerializer

    @action(detail=True, methods=["post"])
    async def assign_perm(self, request, id=None):
        instance = await self.get_object()

        serializer = PermActionSerializer.model_validate(await request.data)

        await assign_perm(
            serializer.perms,
            await User.objects.get(id=serializer.user_id),
            instance,
        )

        return JSONResponse(
            {"message": "Permission assigned successfully."},
            status_code=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    async def remove_perm(self, request, id=None):
        instance = await self.get_object()

        serializer = PermActionSerializer.model_validate(await request.data)

        await remove_perm(
            serializer.perms,
            await User.objects.get(id=serializer.user_id),
            instance,
        )

        return JSONResponse(
            {"message": "Permission removed successfully."},
            status_code=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="perm_assignments")
    async def list_perm_assignments(self, request, id=None):
        instance = await self.get_object()

        UserObjPermsModel = get_user_obj_perms_model_class()
        perms = await UserObjPermsModel.objects.filter(
            content_type=await ContentType.from_model(instance),
            object_id=instance.id,
        ).prefetch_related("user", "permission")

        user_perms_map = defaultdict(list)
        for perm in perms:
            user_perms_map[perm.user_id].append(perm.permission.perm)

        user_objs = {perm.user_id: perm.user for perm in perms}
        result = [
            {
                "user": self.user_serializer.model_validate(user_objs[user_id]),
                "perms": perms_list,
            }
            for user_id, perms_list in user_perms_map.items()
        ]

        return JSONResponse(
            {"data": result},
            status_code=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    async def my_perms(self, request, id=None):
        instance = await self.get_object()

        UserObjPermsModel = get_user_obj_perms_model_class()
        perms = await UserObjPermsModel.objects.filter(
            user=request.user,
            content_type=await ContentType.from_model(instance),
            object_id=instance.id,
        ).prefetch_related("permission")

        return JSONResponse(
            {"perms": [perm.permission.perm for perm in perms]},
            status_code=status.HTTP_200_OK,
        )
