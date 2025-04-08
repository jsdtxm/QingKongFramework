from fastapp.exceptions import NotAuthenticated
from fastapp.serializers import ModelSerializer
from fastapp.views.viewsets import GenericViewSet
from fastapp.contrib.auth.mixins import AccessMixin


class LoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated."""

    async def dispatch(self, request, *args, **kwargs):
        if request.user is None or not request.user.is_authenticated:
            return self.handle_no_permission()
        return await super().dispatch(request, *args, **kwargs)

