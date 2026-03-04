from fastapp import serializers
from fastapp.contrib.key_auth.models import APIKey


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """
    API Key Create Serializer
    """

    app_key = serializers.CharField(max_length=64, null=True)
    app_secret = serializers.CharField(max_length=64, null=True)

    class Meta:
        model = APIKey


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        exclude = ("app_key", "app_secret")
