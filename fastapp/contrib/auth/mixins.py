from typing import Generic

from tortoise.queryset import MODEL

from fastapp import models
from fastapp.contrib.auth import get_user_model
from fastapp.exceptions import NotAuthenticated
from fastapp.serializers import ModelSerializer
from fastapp.views.viewsets import GenericViewSet

User = get_user_model()


class AccessMixin:
    """
    Abstract CBV mixin that gives access mixins the same customizable
    functionality.
    """

    login_url = None
    permission_denied_message = ""
    raise_exception = False

    def handle_no_permission(self):
        raise NotAuthenticated()


class LoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated."""

    async def dispatch(self, request, *args, **kwargs):
        if request.user is None or not request.user.is_authenticated:
            return self.handle_no_permission()
        return await super().dispatch(request, *args, **kwargs)


class SuperUserRequiredMixin(AccessMixin):
    """Verify that the current user is administrator."""

    async def dispatch(self, request, *args, **kwargs):
        if (
            request.user is None
            or not request.user.is_authenticated
            or not request.user.is_superuser
        ):
            return self.handle_no_permission()
        return await super().dispatch(request, *args, **kwargs)


class ReadonlyOrSuperUserMixin(AccessMixin):
    """Verify that the current user is administrator."""

    async def dispatch(self, request, *args, **kwargs):
        if self.action in {"create", "update", "destroy"} and (
            request.user is None
            or not request.user.is_authenticated
            or not request.user.is_superuser
        ):
            return self.handle_no_permission()
        return await super().dispatch(request, *args, **kwargs)


class CreatorMixin(Generic[MODEL]):
    creator_field = "created_by_id"

    async def perform_create(
        self: "GenericViewSet", serializer: ModelSerializer
    ) -> MODEL:
        if self.request.user:
            setattr(serializer, self.creator_field, self.request.user.id)  # type: ignore[attr-defined]
        else:
            setattr(serializer, self.creator_field, None)  # type: ignore[attr-defined]
        return await super().perform_create(serializer)


class CreatorWithFilterMixin(LoginRequiredMixin, CreatorMixin):
    async def filter_queryset(self, queryset):
        queryset = await super().filter_queryset(queryset)

        assert self.request.user
        if self.request.user.is_superuser:
            return queryset

        queryset = queryset.filter(**{self.creator_field: self.request.user.id})
        return queryset


class ModelCreatorMixin:
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="created_{model}s"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class UpdaterMixin:
    updater_field = "updated_by_id"

    async def perform_update(self, serializer) -> None:
        if self.request.user:
            setattr(serializer, self.updater_field, self.request.user.id)  # type: ignore[attr-defined]
        else:
            setattr(serializer, self.updater_field, None)  # type: ignore[attr-defined]
        await super().perform_update(serializer)


class ModelUpdaterMixin:
    updated_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="updated_{model}s"
    )
    updated_at = models.DateTimeField(auto_now=True)


class UserAuditMixin(UpdaterMixin, CreatorMixin[MODEL]):
    pass


class ModelUserAuditMixin(ModelCreatorMixin, ModelUpdaterMixin):
    pass
