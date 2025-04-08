from fastapp.registry import views
from fastapp.router import path, include

urlpatterns = [
    path("", include(views.router)),
]
