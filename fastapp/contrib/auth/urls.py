from fastapp.contrib.auth import views
from fastapp.contrib.auth.views import token_router
from fastapp.router import include, path

urlpatterns = [
    path("", include(token_router)),
    path("group", views.GroupViewSet.as_view()),
]
