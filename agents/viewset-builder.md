# If you will create new ModelViewSet, you should follow this class template.
```
from fastapp.filters import FilterBackend
from fastapp.views.viewsets import ModelViewSet

from apps.{package_name}.models import Document
from apps.{package_name}.serializers import DocumentSerializer
from apps.{package_name}.filters import DocumentFilterSet

class DocumentViewSet(ModelViewSet):
    """
    A viewset for managing documents. It provides standard CRUD operations
    and integrates with filters to retrieve specific documents.
    When a document is deleted, it is marked as deleted instead of being
    permanently removed from the database.
    """

    queryset = Document
    serializer_class = DocumentSerializer
    # Optional, add below lines to enable filter
    filter_backends = [FilterBackend]
    filterset_class = DocumentFilterSet
```

# Here is some mixin class to enhance viewset.
```
from fastapp.contrib.auth.mixins import (
    CreatorMixin,   # Add creator field to the model.
    CreatorWithFilterMixin,   # Add creator field to the model, and filter by creator.
    LoginRequiredMixin, # Check if the user is authenticated.
    SuperUserRequiredMixin, # Check if the user is a superuser.
)
```
## You can use these mixin class like this
```
class DocumentViewSet(SuperUserRequiredMixin, CreatorMixin, ModelViewSet):
    pass
```

# After you create a new ModelViewSet, you should add it to the urls.py file in the corresponding app directory.
```
from apps.document import views
from fastapp.router import path

urlpatterns = [
    path("document", views.DocumentViewSet.as_view()),  # add url like this line
]
```


# The code should be placed in the views.py file in the corresponding app directory.
