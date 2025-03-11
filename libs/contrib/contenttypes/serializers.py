from libs import serializers
from libs.contrib.contenttypes.models import ContentType


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
