from fastapp import serializers
from fastapp.contrib.dynamic_rbac.models import DynamicPermission


class DynamicPermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for the DynamicPermission model.
    This serializer is used to convert DynamicPermission model instances into JSON
    and vice versa. It excludes the 'groups' field from the serialization.
    """

    class Meta:
        model = DynamicPermission
        exclude = ["groups"]


class PermIDsSerializer(serializers.Serializer):
    """
    Serializer for a list of permission IDs.
    This serializer is used to validate a list of integer permission IDs.
    """

    perm_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )


class DynamicPermissionCharSerializer(serializers.Serializer):
    """
    Serializer for handling a permission and its target as strings.
    This serializer is used to convert and validate data where the permission and its target are represented as characters.
    """

    perm = serializers.CharField()
    target = serializers.CharField()
