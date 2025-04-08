from fastapp.contrib.xcaptcha import views
from fastapp.router import path

urlpatterns = [
    path("acquire/", views.CaptchaAcquireView.as_view()),
    path("resolve/", views.CaptchaResolveView.as_view()),
]
