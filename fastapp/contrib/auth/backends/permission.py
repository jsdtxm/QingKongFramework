from typing import Iterable, Optional, Type, Union

from fastapp import models
from fastapp.contrib.auth.backends.base import BasePermissionBackend, PrincipalProtocol
from fastapp.contrib.auth.models import AbstractUser, Permission
from fastapp.contrib.contenttypes.models import ContentType
from fastapp.models import Count


class ModelPermissionBackend(BasePermissionBackend):
    @classmethod
    async def has_perm(
        cls,
        principal: PrincipalProtocol,
        perm: str,
        obj: Optional[Union[models.Model, Type[models.Model]]] = None,
    ) -> bool:
        perm_qs = principal.permissions.filter(perm=perm)

        if obj is not None:
            if isinstance(obj, models.Model):
                obj = obj.__class__

            perm_qs = perm_qs.filter(
                content_type__app_label=obj._meta.app, content_type__model=obj.__name__
            )

        if isinstance(principal, AbstractUser):
            group_perm_qs = Permission.objects.filter(
                group_set=principal.groups.all(), perm=perm
            )
            if obj is not None:
                group_perm_qs = group_perm_qs.filter(
                    content_type__app_label=obj._meta.app,
                    content_type__model=obj.__name__,
                )

        return await perm_qs.exists() or await group_perm_qs.exists()

    @classmethod
    async def has_perms(
        cls,
        principal: PrincipalProtocol,
        perm_list: Iterable[str],
        obj: Optional[Union[models.Model, Type[models.Model]]] = None,
    ) -> bool:
        if not isinstance(perm_list, Iterable) or isinstance(perm_list, str):
            raise ValueError("perm_list must be an iterable of permissions.")

        ctype = await ContentType.from_model(obj)
        if isinstance(principal, AbstractUser):
            return (
                await principal.permissions.filter(
                    content_type=ctype,
                    permission__perm__in=perm_list,
                )
                .annotate(perms_count=Count("permission", distinct=True))
                .filter(perms_count=len(perm_list))
                .exists()
            ) or (
                await Permission.objects.filter(
                    group_set__in=principal.groups.all(),
                    content_type=ctype,
                    permission__perm__in=perm_list,
                )
                .annotate(perms_count=Count("permission", distinct=True))
                .filter(perms_count=len(perm_list))
                .exists()
            )

        else:
            return (
                await principal.permissions.filter(
                    content_type=ctype,
                    permission__perm__in=perm_list,
                )
                .annotate(perms_count=Count("permission", distinct=True))
                .filter(perms_count=len(perm_list))
                .exists()
            )

    @classmethod
    async def has_module_perms(
        cls, principal: PrincipalProtocol, app_label: str
    ) -> bool:
        if isinstance(principal, AbstractUser):
            perm_qs = principal.permissions.filter(content_type__app_label=app_label)

            group_perm_qs = Permission.objects.filter(
                group_set=principal.groups.all()
            ).filter(content_type__app_label=app_label)

            return await perm_qs.exists() or await group_perm_qs.exists()

        else:
            perm_qs = principal.permissions.filter(content_type__app_label=app_label)

            return await perm_qs.exists()
