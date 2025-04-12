"""
This module contains custom filter definitions for the User application.

Classes:
- UserFilterSet: Custom FilterSet for filtering User objects.
"""

from fastapp import filters
from fastapp.filters import LookupExprEnum


class UserFilterSet(filters.FilterSet):
    """
    Custom FilterSet for filtering User objects based on various fields.
    """

    username = filters.CharFilter(
        field_name="username", lookup_expr=LookupExprEnum.icontains.value
    )
    email = filters.CharFilter(
        field_name="email", lookup_expr=LookupExprEnum.icontains.value
    )
