from libs.registry import views
from libs.router import path, include

urlpatterns = [
    path("", include(views.router)),
]
