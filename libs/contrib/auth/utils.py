from enum import Enum
from typing import Annotated, Awaitable, Callable, Optional, Type

import jwt
from async_lru import alru_cache
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError

from common.settings import settings
from libs.contrib.auth.typing import UserProtocol
from libs.django.hashers import check_password
from libs.exceptions import ImproperlyConfigured
from libs.security.jwt import ALGORITHM, global_bearer_token_header
from libs.utils.module_loading import import_string

ANONYMOUS_USERNAME = "anonymous"


class TokenTypeEnum(Enum):
    ACCESS = "access"
    REFRESH = "refresh"


decode = jwt.decode


def get_user_model() -> Type[UserProtocol]:
    """
    Return the User model that is active in this project.
    """
    try:
        return import_string(settings.AUTH_USER_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL refers to model '%s' that has not been installed"
            % settings.AUTH_USER_MODEL
        )


async def get_anonymous_user():
    return await get_user_model().get(username=ANONYMOUS_USERNAME)


@alru_cache()
async def get_user(username: str) -> "UserProtocol":
    user_model: "UserProtocol" = import_string(settings.AUTH_USER_MODEL)
    if user_model is None:
        raise Exception("AUTH_USER_MODEL IS NOT SET")

    return await user_model.objects.get_or_none(username=username)


def verify_password(plain_password, hashed_password):
    return check_password(
        plain_password,
        hashed_password,
    )


async def authenticate_user(
    username: str,
    password: str,
    user_getter: Callable[[str], Awaitable["UserProtocol"]] = get_user,
    verifier: Callable[[str, str], bool] = verify_password,
) -> UserProtocol:
    user = await user_getter(username)
    if not user:
        return False
    if not verifier(password, user.password):
        return False
    return user


def get_current_user_factory(
    token_type: Optional[TokenTypeEnum] = None, raw: bool = False
):
    async def get_current_user(
        token: Annotated[str, Depends(global_bearer_token_header)],
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload: dict = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[ALGORITHM]
            )
            username: str = payload.get("username")
            if username is None:
                raise credentials_exception
        except InvalidTokenError:
            raise credentials_exception

        if token_type is not None and payload.get("type") != token_type.value:
            raise credentials_exception

        user = await get_user(username=username)

        if user is None or user.is_active is False:
            raise credentials_exception

        if raw:
            return (payload, user)

        return user

    return get_current_user


CurrentUser = Annotated[
    UserProtocol, Depends(get_current_user_factory(TokenTypeEnum.ACCESS))
]
RefreshTokenUser = Annotated[
    UserProtocol, Depends(get_current_user_factory(TokenTypeEnum.REFRESH))
]
RawToken = Annotated[UserProtocol, Depends(get_current_user_factory(raw=True))]
