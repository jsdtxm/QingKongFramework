from libs.router import include, path
from libs.contrib.auth.views import token_router

urlpatterns = [
    path("", include(token_router)),
]
