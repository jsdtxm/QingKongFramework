from fastapp.contrib.auth.mixins import LoginRequiredMixin
from fastapp.contrib.contenttypes.filters import ContentTypeFilterSet
from fastapp.contrib.contenttypes.models import ContentType
from fastapp.contrib.contenttypes.serializers import ContentTypeSerializer
from fastapp.filters import FilterBackend
from fastapp.views.viewsets import ReadOnlyModelViewSet


class ContentTypeViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    queryset = ContentType
    serializer_class = ContentTypeSerializer
    filter_backends = [FilterBackend]
    filterset_class = ContentTypeFilterSet
