from fastapp.permissions.base import (
    SAFE_METHODS,
    OperablePermissionBase,
    OperablePermissionMeta,
)
from fastapp.requests import DjangoStyleRequest


class AllowAny(OperablePermissionBase, metaclass=OperablePermissionMeta):
    """
    Allow any access.
    """

    async def has_object_permission(
        self, request: DjangoStyleRequest, view, obj=None
    ) -> bool:
        return True


class IsAuthenticated(OperablePermissionBase, metaclass=OperablePermissionMeta):
    """
    Allows access only to authenticated users.
    """

    async def has_object_permission(
        self, request: DjangoStyleRequest, view, obj=None
    ) -> bool:
        return getattr(request, "user", None) is not None


class IsAdminUser(OperablePermissionBase, metaclass=OperablePermissionMeta):
    """
    Allows access only to admin users.
    """

    async def has_object_permission(
        self, request: DjangoStyleRequest, view, obj=None
    ) -> bool:
        return bool(
            request.user and request.user.is_active and request.user.is_superuser
        )


class IsAuthenticatedOrReadOnly(
    OperablePermissionBase, metaclass=OperablePermissionMeta
):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    async def has_object_permission(
        self, request: DjangoStyleRequest, view, obj=None
    ) -> bool:
        return bool(
            request.method in SAFE_METHODS
            or request.user
            and request.user.is_active
            and request.user.is_authenticated
        )
