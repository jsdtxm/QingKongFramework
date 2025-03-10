from libs import serializers
from libs.contrib.key_auth.models import APIKey


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
