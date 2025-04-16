from pydantic import field_validator

from fastapp import serializers
from fastapp.contrib.auth.models import Group
from fastapp.contrib.auth.utils import get_user_model
from fastapp.contrib.auth.validators import (
    email_validator,
    password_validator,
    username_validator,
)

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
        return username_validator(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        return password_validator(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return email_validator(v)

    class Meta:
        model = User
        fields = ["username", "password", "email"]


class AdminPasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing admin user passwords.

    This serializer is used to validate password change requests for admin users.
    """

    new_password = serializers.CharField(required=True, min_length=8)
