from libs.contrib.xcaptcha import views
from libs.router import path

urlpatterns = [
    path("acquire/", views.CaptchaAcquireView.as_view()),
    path("resolve/", views.CaptchaResolveView.as_view()),
]
