import base64
import hashlib
import re
from enum import Enum
from typing import Annotated, Awaitable, Callable, Optional, Type

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError

from common.settings import settings
from fastapp.contrib.auth.typing import UserProtocol
from fastapp.django.hashers import check_password
from fastapp.exceptions import ImproperlyConfigured
from fastapp.security.jwt import ALGORITHM, global_bearer_token_header
from fastapp.utils.module_loading import import_string

ANONYMOUS_USERNAME = "anonymous"


class TokenTypeEnum(Enum):
    ACCESS = "acc"
    REFRESH = "ref"


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


async def get_user(username: str) -> Optional["UserProtocol"]:
    user_model: "UserProtocol" = import_string(settings.AUTH_USER_MODEL)
    if user_model is None:
        raise Exception("AUTH_USER_MODEL IS NOT SET")
    user = await user_model.objects.get_or_none(username=username)

    if user and not user.is_active:
        return None

    return user


def validate_password_format(password: str):
    """
    Validate the format of a password.
    """

    if not password:
        raise ValueError("Password cannot be empty.")

    # 密码复杂度规则：
    # 1. 至少8个字符
    # 2. 至少包含一个大写字母
    # 3. 至少包含一个小写字母
    # 4. 至少包含一个数字
    # 5. 至少包含一个特殊字符（如 !@#$%^&*()-_=+[]{}|;:'",.<>/?）
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*()\-_=+$${}|;:'\",.<>/?]", password):
        raise ValueError("Password must contain at least one special character.")

    return password


def verify_password(plain_password, hashed_password):
    return check_password(
        plain_password,
        hashed_password,
    )


async def authenticate_user(
    username: str,
    password: str,
    user_getter: Callable[[str], Awaitable[Optional["UserProtocol"]]] = get_user,
    verifier: Callable[[str, str], bool] = verify_password,
) -> Optional[UserProtocol]:
    user = await user_getter(username)
    if not user:
        return None
    if not verifier(password, user.password):
        return None
    return user


def get_current_user_factory(
    token_type: Optional[TokenTypeEnum] = None,
    raw: bool = False,
    raise_exception: bool = True,
    extra_action: Optional[Callable] = None,
    version_checker: Optional[Callable] = None,
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
            payload: dict[str, str] = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[ALGORITHM]
            )
            if token_type is not None and payload.get("typ") != token_type.value:
                raise credentials_exception

            username = payload.get("sub")
            if username is None:
                raise credentials_exception

            user = await get_user(username=username)
            if user is None or user.is_active is False:
                raise credentials_exception

            if version_checker:
                if not version_checker(user, payload.get("ver")):
                    raise credentials_exception
        except (InvalidTokenError, HTTPException):
            if raise_exception:
                raise credentials_exception
            else:
                return (None, None) if raw else None

        if extra_action is not None:
            return extra_action(token_type, raw, raise_exception, payload, user)

        return (payload, user) if raw else user

    return get_current_user


def default_version_checker(user: UserProtocol, ver: str):
    return (
        base64.b85encode(hashlib.blake2s(user.password.encode()).digest()).decode(
            "utf-8"
        )
        == ver
    )


def is_superuser(
    token_type: Optional[TokenTypeEnum],
    raw: bool,
    raise_exception: bool,
    payload: dict[str, str],
    user: UserProtocol,
):
    try:
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        return (None, None) if raw else None


CurrentUser = Annotated[
    UserProtocol,
    Depends(
        get_current_user_factory(
            TokenTypeEnum.ACCESS, version_checker=default_version_checker
        )
    ),
]
CurrentSuperUser = Annotated[
    UserProtocol,
    Depends(
        get_current_user_factory(
            TokenTypeEnum.ACCESS,
            extra_action=is_superuser,
            version_checker=default_version_checker,
        )
    ),
]
OptionalCurrentUser = Annotated[
    Optional[UserProtocol],
    Depends(
        get_current_user_factory(
            TokenTypeEnum.ACCESS,
            raise_exception=False,
            version_checker=default_version_checker,
        )
    ),
]
RefreshTokenUser = Annotated[
    UserProtocol,
    Depends(
        get_current_user_factory(
            TokenTypeEnum.REFRESH, version_checker=default_version_checker
        )
    ),
]
RawToken = Annotated[
    UserProtocol,
    Depends(
        get_current_user_factory(raw=True, version_checker=default_version_checker)
    ),
]
