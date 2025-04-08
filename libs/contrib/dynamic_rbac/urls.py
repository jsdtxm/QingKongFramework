from libs.contrib.dynamic_rbac import views
from libs.router import path

urlpatterns = [
    path("dynamic_permission", views.DynamicPermissionViewSet.as_view()),
]
