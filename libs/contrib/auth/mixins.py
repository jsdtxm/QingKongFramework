from libs.exceptions import NotAuthenticated
from libs.serializers import ModelSerializer
from libs.views.viewsets import GenericViewSet


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

    def dispatch(self, request, *args, **kwargs):
        if request.user is None or not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class SuperUserRequiredMixin(AccessMixin):
    """Verify that the current user is administrator."""

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user is None
            or not request.user.is_authenticated
            or not request.user.is_superuser
        ):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CreatorMixin:
    creator_field = "created_by_id"

    async def perform_create(self: "GenericViewSet", serializer: ModelSerializer):
        if self.request.user:
            setattr(serializer, self.creator_field, self.request.user.id)  # type: ignore[attr-defined]
        else:
            setattr(serializer, self.creator_field, None)  # type: ignore[attr-defined]
        await serializer.save()


class CreatorWithFilterMixin(LoginRequiredMixin, CreatorMixin):
    async def filter_queryset(self, queryset):
        assert self.request.user
        queryset = queryset.filter(**{self.creator_field: self.request.user.id})
        return queryset
