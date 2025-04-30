from fastapp import filters
from fastapp.contrib.contenttypes.models import ContentType


class ContentTypeFilterSet(filters.FilterSet):
    """
    FilterSet for the ContentType model.
    """

    class Meta:
        model = ContentType
