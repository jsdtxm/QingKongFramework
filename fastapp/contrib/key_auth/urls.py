from fastapp.contrib.key_auth.views import APIKeyViewSet, token_router
from fastapp.router import include, path

urlpatterns = [
    path("", include(token_router)),
    path("key", APIKeyViewSet.as_view()),
]
