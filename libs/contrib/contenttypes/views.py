from libs.contrib.auth.mixins import LoginRequiredMixin
from libs.contrib.contenttypes.models import ContentType
from libs.contrib.contenttypes.serializers import ContentTypeSerializer
from libs.views.viewsets import ReadOnlyModelViewSet


class ContentTypeViewSet(LoginRequiredMixin, ReadOnlyModelViewSet):
    queryset = ContentType
    serializer_class = ContentTypeSerializer
