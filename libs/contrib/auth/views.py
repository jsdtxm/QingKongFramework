from datetime import timedelta

from fastapi.routing import APIRouter
from pydantic import BaseModel

from common.settings import settings
from libs.contrib.auth import authenticate_user
from libs.contrib.auth.utils import (
    RawToken,
    RefreshTokenUser,
    CurrentUser,
    TokenTypeEnum,
)
from libs.exceptions import HTTPException
from libs.security.jwt import create_token
from libs.contrib.auth.serializers import UserSerializer

token_router = APIRouter(
    tags=["Auth"]
)


class TokenObtainReq(BaseModel):
    username: str
    password: str


@token_router.post("/token")
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


@token_router.post("/token/refresh")
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


@token_router.post("/token/verify")
async def token_verify(data: RawToken):
    payload, user = data

    return {"payload": payload, "user": user.username}


@token_router.get("/profile")
async def profile(user: CurrentUser):
    return UserSerializer.model_validate(user)
