from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError

from common.settings import settings
from libs.contrib.auth.typing import UserProtocol
from libs.contrib.key_auth.models import APIKey
from libs.security.jwt import ALGORITHM, global_bearer_token_header


def get_api_key_factory(
    raw: bool = False,
    raise_exception: bool = True,
    return_user: bool = False,
):
    async def get_api_key(
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
            uuid = payload.get("uuid")
            if uuid is None:
                if raise_exception:
                    raise credentials_exception
                else:
                    return None
        except InvalidTokenError:
            if raise_exception:
                raise credentials_exception
            else:
                return None

        api_key = await APIKey.objects.get_or_none(uuid=uuid)

        if api_key is None or api_key.is_active is False:
            if raise_exception:
                raise credentials_exception
            else:
                return None

        if return_user:
            return api_key.user

        if raw:
            return (payload, api_key)

        return api_key

    return get_api_key


OptionalApiKey = Annotated[
    Optional[APIKey],
    Depends(get_api_key_factory(raise_exception=False)),
]

OptionalApiKeyUser = Annotated[
    Optional[UserProtocol],
    Depends(get_api_key_factory(raise_exception=False, return_user=True)),
]

RawApiKey = Annotated[APIKey, Depends(get_api_key_factory(raw=True))]
