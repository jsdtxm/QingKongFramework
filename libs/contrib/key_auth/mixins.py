from libs.exceptions import NotAuthenticated
from libs.serializers import ModelSerializer
from libs.views.viewsets import GenericViewSet
from libs.contrib.auth.mixins import AccessMixin


class LoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated."""

    def dispatch(self, request, *args, **kwargs):
        if request.user is None or not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

