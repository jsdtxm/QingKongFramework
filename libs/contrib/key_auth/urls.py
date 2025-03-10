from libs.contrib.key_auth.views import APIKeyViewSet, token_router
from libs.router import include, path

urlpatterns = [
    path("", include(token_router)),
    path("key", APIKeyViewSet.as_view()),
]
