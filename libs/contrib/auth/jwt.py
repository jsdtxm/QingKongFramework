from typing import Annotated

import jwt
from async_lru import alru_cache
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError

from common.settings import settings
from libs.contrib.auth import UserProtocol, get_user_model
from libs.security.jwt import ALGORITHM, global_bearer_token_header
from libs.utils.module_loading import import_string


decode = jwt.decode


User = get_user_model()


@alru_cache()
async def get_user(username: str) -> "UserProtocol":
    user_model: "UserProtocol" = import_string(settings.AUTH_USER_MODEL)
    if user_model is None:
        raise Exception("AUTH_USER_MODEL IS NOT SET")

    return await user_model.objects.get_or_none(username=username)


async def get_current_user(token: Annotated[str, Depends(global_bearer_token_header)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user(username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated["UserProtocol", Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



CurrentUser = Annotated[User, Depends(get_current_active_user)]
