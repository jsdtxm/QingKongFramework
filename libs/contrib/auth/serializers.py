from libs import serializers
from libs.contrib.auth.models import Group
from libs.contrib.auth.utils import get_user_model

User = get_user_model()


# TODO 修改一下User的内置Serializer（Pydantic）排除掉password字段
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("password",)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]
        read_only_fields = ["id"]


class GroupUserSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
