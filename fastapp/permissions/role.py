from fastapp.permissions.base import SAFE_METHODS, BasePermission
from fastapp.requests import DjangoStyleRequest


class AllowAny(BasePermission):
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """

    def has_permission(self, request, view):
        return True


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request: DjangoStyleRequest, view):
        return bool(
            request.user and request.user.is_active and request.user.is_authenticated
        )


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request: DjangoStyleRequest, view):
        return bool(
            request.user and request.user.is_active and request.user.is_superuser
        )


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS
            or request.user
            and request.user.is_active
            and request.user.is_authenticated
        )
