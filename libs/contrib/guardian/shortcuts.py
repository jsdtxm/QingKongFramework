from libs.contrib.auth.typing import UserProtocol
from libs.contrib.contenttypes.models import ContentType
from libs.contrib.guardian.models import GroupObjectPermission, UserObjectPermission
from libs.models import BaseModel, Q, Subquery


async def get_objects_for_user(
    user: UserProtocol,
    perm: str,
    klass: BaseModel = None,
    use_groups=True,
    with_superuser=True,
    accept_model_perms=True,
):
    queryset = klass.objects.all()

    # First check if user is superuser and if so, return queryset immediately
    if with_superuser and user.is_superuser:
        return await queryset

    ctype = await ContentType.from_model(klass)

    if accept_model_perms:
        # TODO group has perm
        if await user.has_perm(perm, klass):
            return await queryset

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

    return await queryset.filter(q)
