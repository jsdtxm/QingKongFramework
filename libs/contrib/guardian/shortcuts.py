from typing import Type

from libs.contrib.auth.models import Group
from libs.contrib.auth.typing import UserProtocol
from libs.contrib.contenttypes.models import ContentType
from libs.models import Model, Q, Subquery
from libs.utils.module_loading import import_string


async def get_objects_for_user(
    user: UserProtocol,
    perm: str,
    klass: Type[Model],
    use_groups=True,
    with_superuser=True,
    accept_model_perms=True,
):
    GroupObjectPermission = import_string(
        "libs.contrib.guardian.models.GroupObjectPermission"
    )
    UserObjectPermission = import_string(
        "libs.contrib.guardian.models.UserObjectPermission"
    )

    queryset = klass.objects.all()

    # First check if user is superuser and if so, return queryset immediately
    if with_superuser and user.is_superuser:
        return queryset

    ctype = await ContentType.from_model(klass)

    if accept_model_perms:
        # TODO group has perm
        if await user.has_perm(perm, klass):
            return queryset

    # Now we should extract list of pk values for which we would filter
    # queryset
    user_obj_perms_queryset = UserObjectPermission.objects.filter(
        user=user,
        content_type=ctype,
        permission__perm=perm,
    )

    q = Q(id__in=Subquery(user_obj_perms_queryset.values("object_id")))

    if use_groups:
        groups_obj_perms_queryset = GroupObjectPermission.objects.filter(
            group__user_set=user,
            content_type=ctype,
            permission__perm=perm,
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
        "libs.contrib.guardian.models.GroupObjectPermission"
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
