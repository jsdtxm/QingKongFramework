from typing import TYPE_CHECKING, Iterable, Optional, Protocol, Type, Union

from fastapp import models

if TYPE_CHECKING:
    from fastapp.models.model import Model


class PrincipalProtocol(Protocol):
    permissions: models.ManyToManyRelation


class BasePermissionBackend:
    @classmethod
    async def has_perm(
        cls,
        principal: PrincipalProtocol,
        perm: str,
        obj: Optional[Union["Model", Type["Model"]]] = None,
    ) -> bool:
        pass

    @classmethod
    async def has_perms(
        cls,
        principal: PrincipalProtocol,
        perm_list: Iterable[str],
        obj: Optional[Union["Model", Type["Model"]]] = None,
    ) -> bool:
        pass

    @classmethod
    async def has_module_perms(
        cls, principal: PrincipalProtocol, app_label: str
    ) -> bool:
        pass
