from libs.contrib.dynamic_rbac import views
from libs.contrib.dynamic_rbac.views import dynamic_rbac_router
from libs.router import include, path

urlpatterns = [
    path("", include(dynamic_rbac_router)),
    path("dynamic_permission", views.DynamicPermissionViewSet.as_view()),
    path("group", views.DynamicPermissionViewSet.as_view()),
]
