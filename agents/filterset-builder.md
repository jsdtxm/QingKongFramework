# If you will create new FilterSet, you should follow this class template.
```
from fastapp import filters
from apps.{package_name}.models import ModuleAction

class ModuleNodeFilterSet(filters.FilterSet):
    """
    A filter set for querying ModuleNode model instances.
    This filter set allows users to filter ModuleNode records based on specific fields and lookup expressions.
    """

    class Meta:
        model = ModuleNode
```

# If you will add filterset to a ViewSet, you should follow these code.
```
from fastapp.filters import FilterBackend
from apps.{package_name}.filters import ModuleActionFilterSet

class ModuleActionViewSet(ModelViewSet):
    queryset = ModuleAction
    serializer_class = ModuleActionSerializer
    filter_backends = [FilterBackend]    # add this
    filterset_class = ModuleActionFilterSet  # add this
```
## before you add filterset to a ViewSet, you should take a look at what's in the filters.py in the corresponding app directory.


# The code should be placed in the filters.py file in the corresponding app directory.
