from datetime import timedelta

from fastapi import Request, Response
from pydantic import BaseModel, field_validator
from starlette import status

from common.settings import settings
from libs.contrib.auth import authenticate_user
from libs.contrib.auth.mixins import SuperUserRequiredMixin
from libs.contrib.auth.models import Group
from libs.contrib.auth.serializers import (
    GroupSerializer,
    GroupUserSerializer,
    UserSerializer,
)
from libs.contrib.auth.utils import (
    CurrentUser,
    RawToken,
    RefreshTokenUser,
    TokenTypeEnum,
    get_user_model,
)
from libs.django.hashers import make_password
from libs.exceptions import HTTPException
from libs.responses import JSONResponse
from libs.router import APIRouter
from libs.security.jwt import create_token
from libs.views import viewsets
from libs.views.decorators import action

User = get_user_model()

token_router = APIRouter(tags=["Auth"])


class TokenObtainReq(BaseModel):
    """
    A Pydantic model representing a request to obtain an authentication token.
    It contains the necessary fields for user authentication.

    Attributes:
        username (str): The username of the user trying to obtain a token.
        password (str): The password of the user trying to obtain a token.
    """
    username: str
    password: str


@token_router.post("/token/")
async def token_obtain(req: TokenObtainReq):
    """
    Obtain an access token and a refresh token for a user.

    Args:
        req (TokenObtainReq): A request object containing the user's username and password.

    Returns:
        dict: A dictionary containing the access token and the refresh token.

    Raises:
        HTTPException: If the provided login credentials are invalid.
    """
    user = await authenticate_user(req.username, req.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    access_token = create_token(
        {"type": TokenTypeEnum.ACCESS.value, "username": user.username},
        timedelta(seconds=settings.ACCESS_TOKEN_LIFETIME),
    )
    refresh_token = create_token(
        {"type": TokenTypeEnum.REFRESH.value, "username": user.username},
        timedelta(seconds=settings.REFRESH_TOKEN_LIFETIME),
    )

    return {
        "access": access_token,
        "refresh": refresh_token,
    }


@token_router.post("/token/refresh/")
async def token_refresh(user: RefreshTokenUser):
    """
    Refresh the access token for a user.

    Args:
        user (RefreshTokenUser): A user object containing the necessary information to refresh the token.

    Returns:
        dict: A dictionary containing the new access token.

    Raises:
        HTTPException: If the user is inactive or the provided credentials are invalid.
    """
    # TODO 如果用户修改密码，这里实际上不能处理好
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    access_token = create_token(
        {"type": TokenTypeEnum.ACCESS.value, "username": user.username},
        timedelta(seconds=settings.ACCESS_TOKEN_LIFETIME),
    )

    return {
        "access": access_token,
    }


@token_router.post("/token/verify/")
async def token_verify(data: RawToken):
    """
    Verify the authenticity of a token.

    Args:
        data (RawToken): The raw token data to be verified.

    Returns:
        dict: A dictionary containing the token payload and the username of the associated user.

    Raises:
        HTTPException: If the token is invalid or the user is inactive.
    """
    payload, user = data

    return {"payload": payload, "user": user.username}


@token_router.get("/profile/")
async def profile(user: CurrentUser):
    """
    Retrieve the user profile information.

    Args:
        user (CurrentUser): The current authenticated user.

    Returns:
        UserSerializer: A serialized representation of the user's profile.
    """
    return UserSerializer.model_validate(user)


class PasswordUpdate(BaseModel):
    """
    A Pydantic model representing a request to update a user's password.

    Attributes:
        old_password (str): The user's current password.
        new_password (str): The new password the user wants to set.
    """
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str):
        """
        Validate the new password to ensure it meets the complexity requirements.

        Args:
            v (str): The new password to be validated.

        Returns:
            str: The validated new password.

        Raises:
            ValueError: If the password does not meet the complexity requirements.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain a number")
        if not any(char.islower() for char in v) and not any(
            char.isupper() for char in v
        ):
            raise ValueError("Password must contain a letter")
        if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/~`" for char in v):
            raise ValueError("Password must contain a special character")
        return v


@token_router.post("/change-password/")
async def change_password(user: CurrentUser, req: PasswordUpdate):
    """
    Change the user's password.

    Args:
        user (CurrentUser): The current authenticated user.
        req (PasswordUpdate): A request object containing the old and new passwords.

    Returns:
        dict: A dictionary containing a success message.

    Raises:
        HTTPException: If the provided old password is invalid.
        ValueError: If the new password contains the username.
    """
    user = await authenticate_user(user.username, req.old_password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    if user.username in req.new_password:
        raise ValueError("Password cannot contain the username")

    user.password = make_password(req.new_password)
    await user.save()

    return {"msg": "Password updated successfully"}


@token_router.post("/logout/")
async def logout(user: CurrentUser, request: Request, response: Response):
    """
    Log out the current user by deleting all cookies from the response.

    Args:
        user (CurrentUser): The current authenticated user.
        request (Request): The incoming request object.
        response (Response): The outgoing response object.

    Returns:
        dict: A dictionary containing a success message.
    """
    cookies = request.cookies

    for key in cookies.keys():
        response.delete_cookie(key=key)

    return {"msg": "Logout successfully"}


class GroupViewSet(SuperUserRequiredMixin, viewsets.ModelViewSet):
    """
    A viewset for handling Group model operations.

    This viewset inherits from SuperUserRequiredMixin and ModelViewSet, which means
    only superusers can access its endpoints. It provides a set of actions for
    creating, retrieving, updating, and deleting Group instances, as well as
    managing the users associated with a group.

    Attributes:
        queryset (QuerySet): The queryset of Group objects to be used by the viewset.
        serializer_class (Serializer): The serializer class to be used for serializing
                                       and deserializing Group instances.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    @action(detail=True, methods=["get"], url_path="user")
    async def list_users(self, request, id=None):
        """
        List all users associated with a specific group.

        Args:
            request (Request): The incoming request object.
            id (int, optional): The ID of the group. Defaults to None.

        Returns:
            JSONResponse: A JSON response containing the serialized list of users.
        """
        group = await self.get_object()
        user_set = await group.user_set.all()

        serializer = viewsets.ListSerializerWrapper(
            [UserSerializer.model_validate(x) for x in user_set]
        )

        return JSONResponse(serializer.model_dump())

    @action(detail=True, methods=["post"], url_path="user")
    async def add_users(self, request, id=None):
        """
        Add users to a specific group.

        Args:
            request (Request): The incoming request object.
            id (int, optional): The ID of the group. Defaults to None.

        Returns:
            JSONResponse: A JSON response indicating the success of the operation.

        Raises:
            Exception: If an error occurs during the operation.
        """
        group = await self.get_object()

        try:
            serializer = GroupUserSerializer.model_validate(await request.data)
            users = await User.objects.filter(id__in=serializer.user_ids)
            await group.user_set.add(*users)
            return JSONResponse(
                {
                    "msg": "ok",
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            raise e

    @action(detail=True, methods=["delete"], url_path="user")
    async def remove_users(self, request, id=None):
        """
        Remove users from a specific group.

        Args:
            request (Request): The incoming request object.
            id (int, optional): The ID of the group. Defaults to None.

        Returns:
            JSONResponse: A JSON response indicating the success of the operation.

        Raises:
            Exception: If an error occurs during the operation.
        """
        group = await self.get_object()

        try:
            serializer = GroupUserSerializer.model_validate(await request.data)

            users = await User.objects.filter(id__in=serializer.user_ids)
            await group.user_set.remove(*users)
            return JSONResponse(
                {
                    "msg": "ok",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            raise e
