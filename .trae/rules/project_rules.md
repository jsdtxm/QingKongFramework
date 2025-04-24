# Framework
Develop using our self-developed fastapp framework called `fastapp`.
This framework is built on top of FastApi, and we do something to make it looks like a full async Django and Django REST Framework.
We don't need to use decorator like `sync_to_async`, and don't use `aget` or `afilter` for asynchronous purposes on ORM.

## view example
### File place in project_folder/apps/{app_name}/views.py
```python
from fastapp.contrib.auth.mixins import CreatorMixin, SuperUserRequiredMixin
from fastapp.filters import FilterBackend
from fastapp.views.viewsets import ModelViewSet

from apps.document.models import Folder
from apps.document.serializers import FolderSerializer
from apps.document.filters import FolderFilterSet

class FolderViewSet(SuperUserRequiredMixin, CreatorMixin, ModelViewSet):
    queryset = Folder
    serializer_class = FolderSerializer
    # Optional, add below lines to enable filter
    filter_backends = [FilterBackend]
    filterset_class = FolderFilterSet

    @action(detail=True, methods=["get"], url_path="children")
    async def list_sub_folder(self, request: DjangoStyleRequest, id: int):
        folder = await self.get_object()
        sub_folders = await folder.children.all()

        serializer = viewsets.ListSerializerWrapper(
            [FolderSerializer.model_validate(x) for x in sub_folders]
        )

        return JSONResponse(serializer.model_dump())

    async def perform_destroy(self, instance):
        instance.is_deleted = True
        await instance.save()
```

## url example
### File place in project_folder/apps/{app_name}/urls.py
```python
from apps.document import views
from fastapp.router import path

urlpatterns = [
    path("folder", views.FolderViewSet.as_view()),
    path("document", views.DocumentViewSet.as_view()),
]
```

## serializer example
### File place in project_folder/apps/{app_name}/serializers.py
```python
"""
Serializers for the Document application.

This module contains serializers for the Document and DocumentVersion models.
"""

from apps.document.models import Document, DocumentVersion, Folder
from apps.misc.serializers import TagSerializer
from fastapp import serializers

class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField()
    tag_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)


class DocumentCreateSerializer(serializers.ModelSerializer):
    category = MaterialCategorySerializer(null=True)    # Nested ModelSerializer should set null=True.

    class Meta:
        model = Document
        read_only_fields = ["is_deleted", "current_version"]
```

## model example
### File place in project_folder/apps/{app_name}/models.py
```python
from fastapp import models

class Document(models.Model):
    title = models.CharField(max_length=512)
    content = models.TextField()

    folder = models.ForeignKeyField(Folder, related_name="documents")

    current_version = models.IntegerField(default=1)
    versions: models.ReverseRelation["DocumentVersion"]

    tags = models.ManyToManyField(Tag, verbose_name="Tags", null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="documents")

    # Optional, add below lines to enable soft delete
    is_deleted = models.BooleanField("Soft Delete", default=False)

    # ForeignKeyField should add index like below lines.
    class Meta:
        indexes = [
            models.Index(fields=("folder_id",)),
            models.Index(fields=("created_by_id",)),
        ]
```

## filter example
### File place in project_folder/apps/{app_name}/filters.py
```python
from apps.document.models import Document, Folder
from fastapp import filters
from fastapp.filters import LookupExprEnum
from pydantic import field_validator

class FolderFilterSet(filters.FilterSet):

    # Optional, if you want to add custom field level validation, you can add below lines.
    @field_validator("name")
    def validate_name(cls, value):
        if len(name) < 2:
            raise ValueError("Invalid name.")

        return value

    # Optional, if you want to add custom model level validation, you can add below lines.
    @model_validator(mode="after")
    def check_username_or_email_or_phone(self):
        if not self.username and not self.email and not self.phone:
            raise ValueError("At least one of username, email, or phone is required")
        return self

    class Meta:
        model = Folder
        # Optional, if you want to specify filter method.
        fields = {
            "name": LookupExprEnum.contains.value,  # Default is "exact".
            "created_at": [LookupExprEnum.gte.value, LookupExprEnum.lte.value], # Support multiple lookup expressions.
        }
        # Optional, if you want to specify fields to exclude, you can add below lines.
        exclude = []    # All fields will be enabled if you don't specify here.

```

## fixtures example
### File place in project_folder/apps/{app_name}/fixtures/{fixture_order}_{fixture_name}.json
```json
[
  {
    "model": "misc.Tag",
    "pk": 1,
    "fields": {
      "namespace": "warehouse",
      "key": "transfer",
      "label": "中转",
      "created_by_id": 1    // ForeignKeyField should add _id suffix.
    }
  },
  {
    "model": "misc.Tag",
    "pk": 2,
    "fields": {
      "namespace": "warehouse",
      "key": "sample",
      "label": "取样",
      "created_by_id": 1
    }
  }
]
```

## framework cli
- help: `python manage.py --help`
- startapp: `python manage.py startapp {app_name}`

### cli with single process mode
> Note: This mode is only recommended for develop use.
- runserver-aio: `python manage.py runserver-aio`

### cli with micro-service mode
- runserver: `python manage.py runserver`
- gateway: `python manage.py gateway`


## How to start a new app?
### Step 1: Create a new app
```
python manage.py startapp {app_name}
```
### Step 2: Add the app to the INSTALLED_APPS in settings.py
```python
INSTALLED_APPS = [
    # ...
    "apps.{app_name}",
]
```

# Documentation
- You should add class docstring to your model, serializer, filterset, and viewset.
- You should add function docstring to your function.
- All document should be written in English and keep it professional and clear, don't write doc for params and returns.

# Testing
Todo, you can ignore this part.