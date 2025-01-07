from typing import Iterable, Optional, Type, Union

from libs import models
from libs.contrib.auth.backends.permission import (
    ModelPermissionBackend,
    PrincipalProtocol,
)
from libs.contrib.auth.models import AbstractUser
from libs.contrib.contenttypes.models import ContentType
from libs.contrib.guardian.models import GroupObjectPermission, UserObjectPermission
from libs.models import Count


class ObjectPermissionBackend(ModelPermissionBackend):
    @classmethod
    async def has_perm(
        cls,
        principal: PrincipalProtocol,
        perm: str,
        obj: Optional[Union[models.Model, Type[models.Model]]] = None,
    ) -> bool:
        if isinstance(obj, type):
            return await super().has_perm(principal, perm, obj)

        if isinstance(principal, AbstractUser):
            ctype = await ContentType.from_model(obj)
            return (
                await UserObjectPermission.objects.filter(
                    user=principal,
                    content_type=ctype,
                    permission__perm=perm,
                    object_id=obj.id,
                ).exists()
            ) or (
                await GroupObjectPermission.objects.filter(
                    group__in=principal.groups.all(),
                    content_type=ctype,
                    permission__perm=perm,
                    object_id=obj.id,
                ).exists()
            )
        else:
            return await GroupObjectPermission.objects.filter(
                group=principal,
                content_type=ctype,
                permission__perm=perm,
                object_id=obj.id,
            ).exists()

        return

    @classmethod
    async def has_perms(
        cls,
        principal: PrincipalProtocol,
        perm_list: Iterable[str],
        obj: Optional[Union[models.Model, Type[models.Model]]] = None,
    ):
        if isinstance(obj, type):
            return await super().has_perms(principal, perm_list, obj)
        
        if not isinstance(perm_list, Iterable) or isinstance(perm_list, str):
            raise ValueError("perm_list must be an iterable of permissions.")

        if isinstance(principal, AbstractUser):
            ctype = await ContentType.from_model(obj)

            return (
                await UserObjectPermission.objects.filter(
                    user=principal,
                    content_type=ctype,
                    permission__perm__in=perm_list,
                    object_id=obj.id,
                )
                .annotate(perms_count=Count("permission", distinct=True))
                .filter(perms_count=len(perm_list))
                .exists()
            ) or (
                await GroupObjectPermission.objects.filter(
                    group__in=principal.groups.all(),
                    content_type=ctype,
                    permission__perm__in=perm_list,
                    object_id=obj.id,
                )
                .annotate(perms_count=Count("permission", distinct=True))
                .filter(perms_count=len(perm_list))
                .exists()
            )

        else:
            return (
                await GroupObjectPermission.objects.filter(
                    group=principal,
                    content_type=ctype,
                    permission__perm__in=perm_list,
                    object_id=obj.id,
                )
                .annotate(perms_count=Count("permission", distinct=True))
                .filter(perms_count=len(perm_list))
                .exists()
            )
