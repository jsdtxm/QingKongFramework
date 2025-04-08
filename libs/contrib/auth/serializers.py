from libs import serializers
from libs.contrib.auth.models import Group
from libs.contrib.auth.utils import get_user_model

User = get_user_model()


# TODO 修改一下User的内置Serializer（Pydantic）排除掉password字段
class UserSerializer(serializers.ModelSerializer):
    """
    A serializer class for the User model.

    This serializer excludes the 'password' field from the serialized output.
    """

    class Meta:
        model = User
        exclude = ("password",)


class GroupSerializer(serializers.ModelSerializer):
    """
    A serializer class for the Group model.

    This serializer includes 'id' and 'name' fields, with 'id' set as read-only.
    """

    class Meta:
        model = Group
        fields = ["id", "name"]
        read_only_fields = ["id"]


class UserIDsSerializer(serializers.Serializer):
    """
    A serializer class for validating a list of user IDs.

    This serializer uses a ListField to ensure that the input is a non-empty list of integers.
    """

    user_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
