from fastapp import filters
from fastapp.contrib.dynamic_rbac.models import DynamicPermission


class DynamicPermissionFilterSet(filters.FilterSet):
    """
    FilterSet for the DynamicPermission model.
    """

    class Meta:
        model = DynamicPermission
