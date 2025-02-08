from libs import serializers
from libs.contrib.auth.utils import get_user_model

User = get_user_model()

# TODO 修改一下User的内置Serializer（Pydantic）排除掉password字段
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("password",)
