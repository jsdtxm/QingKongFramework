from fastapp.contrib.dynamic_rbac import views
from fastapp.contrib.dynamic_rbac.views import dynamic_rbac_router
from fastapp.router import include, path

urlpatterns = [
    path("", include(dynamic_rbac_router)),
    path("dynamic_permission", views.DynamicPermissionViewSet.as_view()),
    path("group", views.AdminGroupWithDynamicPermissionViewSet.as_view()),
    path("permissions", views.CurrentUserDynamicPermissionView.as_view()),
]
