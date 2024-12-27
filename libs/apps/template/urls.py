from apps.app_name import views
from libs.router import include, path

urlpatterns = [
    path("", include(views.router)),
    path("search", views.search, methods=["post"]),
    path("literatures", views.literatures, methods=["get"]),
    path("literatures/{id}/reactions", views.literature_reactions, methods=["get"]),
    path("literatures/{id}/substances", views.literature_substances, methods=["get"]),
    path("reactions", views.reactions, methods=["get"]),
    path("reactions/{id}/conditions", views.reactions_conditions, methods=["get"]),
    path("natures", views.natures, methods=["get"]),
    path("categories", views.CategoriesView.as_view()),
]
