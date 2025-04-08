from typing import TYPE_CHECKING, Type

from fastapp import exceptions
from fastapp.exceptions import Http404
from fastapp.permissions.base import BasePermission

if TYPE_CHECKING:
    from fastapp import models
    from fastapp.models import QuerySet
    from fastapp.views.viewsets import View


class ModelPermissions(BasePermission):
    """
    The request is authenticated using `django.contrib.auth` permissions.
    See: https://docs.djangoproject.com/en/dev/topics/auth/#permissions

    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the model.

    This permission can only be applied against view classes that
    provide a `.queryset` attribute.
    """

    # Map methods into required permission codes.
    # Override this if you need to also provide 'view' permissions,
    # or if you want to provide custom permission codes.
    perms_map = {
        "GET": [],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["add"],
        "PUT": ["change"],
        "PATCH": ["change"],
        "DELETE": ["delete"],
    }

    authenticated_users_only = True

    def get_required_permissions(self, method, model_cls: Type["models.Model"]):
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        return [perm for perm in self.perms_map[method]]

    def _queryset(self, view: "View") -> "QuerySet":
        assert (
            hasattr(view, "get_queryset") or getattr(view, "queryset", None) is not None
        ), (
            "Cannot apply {} on a view that does not set "
            "`.queryset` or have a `.get_queryset()` method."
        ).format(self.__class__.__name__)

        if hasattr(view, "get_queryset"):
            queryset = view.get_queryset()
            assert queryset is not None, "{}.get_queryset() returned None".format(
                view.__class__.__name__
            )
            return queryset
        return view.queryset  # type: ignore

    async def has_permission(self, request, view):
        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False

        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, "_ignore_model_permissions", False):
            return True

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)

        return await request.user.has_perms(perms, queryset.model)


class ModelPermissionsOrAnonReadOnly(ModelPermissions):
    """
    Similar to DjangoModelPermissions, except that anonymous users are
    allowed read-only access.
    """

    authenticated_users_only = False


class ObjectPermissions(ModelPermissions):
    """
    The request is authenticated using Django's object-level permissions.
    It requires an object-permissions-enabled backend, such as Django Guardian.

    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the object using .has_perms.

    This permission can only be applied against view classes that
    provide a `.queryset` attribute.
    """

    def get_required_object_permissions(self, method, model_cls):
        return super().get_required_permissions(method, model_cls)

    async def has_object_permission(self, request, view, obj):
        # authentication checks have already executed via has_permission
        queryset = self._queryset(view)
        model_cls = queryset.model
        user = request.user

        perms = self.get_required_object_permissions(request.method, model_cls)

        if not await user.has_perms(perms, obj):
            raise Http404

        return True
