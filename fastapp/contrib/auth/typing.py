from typing import TYPE_CHECKING, Iterable, Optional, Protocol, Self, Type, Union

if TYPE_CHECKING:
    from fastapp import models
    from fastapp.contrib.auth.models import AbstractUser


class UserProtocol(Protocol):
    id: int
    username: str
    password: str

    is_active: bool
    is_superuser: bool

    objects: "UserProtocol"

    @classmethod
    async def get_or_none(cls, **kwargs) -> Optional[Self]: ...

    @classmethod
    async def get(cls, **kwargs) -> Self: ...

    @property
    def is_authenticated(self) -> bool: ...

    @property
    def is_anonymous(self) -> bool: ...

    async def has_perm(
        self,
        perm: str,
        obj: Optional[Union["models.Model", Type["models.Model"]]] = None,
    ) -> bool: ...

    async def has_perms(
        self,
        perm_list: Iterable[str],
        obj: Optional[Union["models.Model", Type["models.Model"]]] = None,
    ) -> bool: ...

    @classmethod
    async def create_user(
        self, username, email=None, password=None, **extra_fields
    ) -> Self: ...


if TYPE_CHECKING:
    class UserProtocol(AbstractUser, UserProtocol): ...