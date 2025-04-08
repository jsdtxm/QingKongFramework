from libs.contrib.auth import views
from libs.contrib.auth.views import token_router
from libs.router import include, path

urlpatterns = [
    path("", include(token_router)),
    path("group", views.GroupViewSet.as_view()),
]
