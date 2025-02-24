from datetime import timedelta

from pydantic import BaseModel, field_validator

from common.settings import settings
from libs.contrib.auth import authenticate_user
from libs.contrib.auth.serializers import UserSerializer
from libs.contrib.auth.utils import (
    CurrentUser,
    RawToken,
    RefreshTokenUser,
    TokenTypeEnum,
)
from libs.django.hashers import make_password
from libs.exceptions import HTTPException
from libs.router import APIRouter
from libs.security.jwt import create_token

token_router = APIRouter(tags=["Auth"])


class TokenObtainReq(BaseModel):
    username: str
    password: str


@token_router.post("/token/")
async def token_obtain(req: TokenObtainReq):
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
    payload, user = data

    return {"payload": payload, "user": user.username}


@token_router.get("/profile/")
async def profile(user: CurrentUser):
    return UserSerializer.model_validate(user)


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str):
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
    user = await authenticate_user(user.username, req.old_password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

    if user.username in req.new_password:
        raise ValueError("Password cannot contain the username")

    user.password = make_password(req.new_password)
    await user.save()

    return {"msg": "Password updated successfully"}
