from typing import List, Type

from fastapp.contrib.auth.models import Group
from fastapp.contrib.auth.typing import UserProtocol
from fastapp.contrib.contenttypes.models import ContentType
from fastapp.contrib.guardian.utils import (
    get_group_obj_perms_model_class,
    get_identity,
    get_user_obj_perms_model_class,
)
from fastapp.models import BaseModel, Model, Q, Subquery
from fastapp.models.queryset import QuerySet
from fastapp.utils.module_loading import import_string


async def get_objects_for_user(
    user: UserProtocol,
    perms: str | List[str],
    klass: Type[Model] | QuerySet[Model],
    use_groups=True,
    with_superuser=True,
    accept_model_perms=True,
):
    GroupObjectPermission = get_group_obj_perms_model_class()
    UserObjectPermission = get_user_obj_perms_model_class()

    if isinstance(perms, str):
        perms = [perms]

    if len(perms) > 1:
        raise Exception("not support yet")

    perms = perms[0]

    queryset = klass if isinstance(klass, QuerySet) else klass.objects.all()
    klass = klass.model if isinstance(klass, QuerySet) else klass

    # First check if user is superuser and if so, return queryset immediately
    if with_superuser and user.is_superuser:
        return queryset

    ctype = await ContentType.from_model(klass)

    if accept_model_perms:
        # TODO group has perm
        if await user.has_perm(perms, klass):
            return queryset

    # Now we should extract list of pk values for which we would filter
    # queryset
    user_obj_perms_queryset = UserObjectPermission.objects.filter(
        user=user,
        content_type=ctype,
        permission__perm=perms,
    )

    q = Q(id__in=Subquery(user_obj_perms_queryset.values("object_id")))

    if use_groups:
        groups_obj_perms_queryset = GroupObjectPermission.objects.filter(
            group__user_set=user,
            content_type=ctype,
            permission__perm=perms,
        )

        q |= Q(id__in=Subquery(groups_obj_perms_queryset.values("object_id")))

    return queryset.filter(q)


async def get_objects_for_group(
    group: Group,
    perm: str,
    klass: Model,
    accept_model_perms=True,
):
    GroupObjectPermission = import_string(
        "fastapp.contrib.guardian.models.GroupObjectPermission"
    )

    queryset = klass.objects.all()

    ctype = await ContentType.from_model(klass)

    if accept_model_perms:
        # TODO group has perm
        if await group.has_perm(perm, klass):
            return queryset

    # Now we should extract list of pk values for which we would filter
    # queryset
    group_obj_perms_queryset = GroupObjectPermission.objects.filter(
        group=group,
        content_type=ctype,
        permission__perm=perm,
    )

    q = Q(id__in=Subquery(group_obj_perms_queryset.values("object_id")))

    return queryset.filter(q)


async def assign_perm(perms, user_or_group, obj):
    if isinstance(perms, str):
        perms = [perms]

    user, group = get_identity(user_or_group)

    if isinstance(obj, BaseModel):
        obj = [
            obj,
        ]

    PermissionModel = (
        get_user_obj_perms_model_class() if user else get_group_obj_perms_model_class()
    )

    for perm in perms:
        await PermissionModel.objects.bulk_assign_perm(perm, user_or_group, obj)
