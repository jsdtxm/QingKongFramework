import re

from pydantic import field_validator

from fastapp import serializers
from fastapp.contrib.auth.models import Group
from fastapp.contrib.auth.utils import get_user_model

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


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating admin users.

    This serializer is used to validate and create admin user accounts with additional attributes like role, company, and department.
    """

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        # 检查是否为空以及是否符合用户名格式
        if v and not re.match(r"^[a-zA-Z0-9_]{3,20}$", v):
            raise ValueError(
                "Invalid username format. Username must be 3-20 characters long and can only contain letters, numbers, and underscores."
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        # 检查是否为空以及是否符合密码复杂度规则
        if not v:
            raise ValueError("Password cannot be empty.")

        # 密码复杂度规则：
        # 1. 至少8个字符
        # 2. 至少包含一个大写字母
        # 3. 至少包含一个小写字母
        # 4. 至少包含一个数字
        # 5. 至少包含一个特殊字符（如 !@#$%^&*()-_=+[]{}|;:'",.<>/?）
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*()\-_=+$${}|;:'\",.<>/?]", v):
            raise ValueError("Password must contain at least one special character.")

        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v

    class Meta:
        model = User
        fields = ["username", "password", "email"]


class AdminPasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing admin user passwords.

    This serializer is used to validate password change requests for admin users.
    """

    new_password = serializers.CharField(required=True, min_length=8)
