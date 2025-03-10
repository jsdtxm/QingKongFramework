from libs import serializers
from libs.contrib.key_auth.models import APIKey


class APIKeyCreateSerializer(serializers.ModelSerializer):
    key = serializers.CharField(null=True)

    class Meta:
        model = APIKey
        hidden_fields = ("uuid",)


class APIKeySerializer(serializers.ModelSerializer):

    class Meta:
        model = APIKey
