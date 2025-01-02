from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Callable, Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.api_key import APIKeyBase
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel, Field, field_validator
from starlette.status import HTTP_401_UNAUTHORIZED
from typing_extensions import Doc

from common.settings import settings
from libs.security.api_key import api_key_auth_factory, key_handler

ALGORITHM = "HS256"


class GlobalBearerTokenHeader(APIKeyBase):
    def __init__(
        self,
        *,
        scheme_name: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme description.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        auto_error: Annotated[
            bool,
            Doc(
                """
                By default, if the header is not provided, `APIKeyHeader` will
                automatically cancel the request and send the client an error.

                If `auto_error` is set to `False`, when the header is not available,
                instead of erroring out, the dependency result will be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, in a header or
                in an HTTP Bearer token).
                """
            ),
        ] = True,
    ):
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.header},  # type: ignore[arg-type]
            name="Authorization",
            description=description,
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get(self.model.name)
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"Authenticate": "Bearer"},
                )
            else:
                return None
        return param


global_bearer_token_header = GlobalBearerTokenHeader(auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))

    to_encode = data.copy()
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def jwt_validator(request: Request, token: str) -> Any:  # pylint: disable=W0613
    """jwt_validator"""

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM], verify=True)

    return payload


# auth in openapi global
JwtAuth = Annotated[
    dict, Depends(api_key_auth_factory(jwt_validator, global_bearer_token_header))
]


class IndividualAPIKey(BaseModel):
    Authorization: str = Field(default="Bearer ")

    @field_validator("Authorization")
    @classmethod
    def valid_token(cls, v):
        scheme, param = get_authorization_scheme_param(v)
        if not v or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"Authenticate": "Bearer"},
            )

        return param


def individual_jwt_auth_factory(inner: Callable[[Request, str], bool]):
    async def auth_func(
        request: Request, headers: Annotated[IndividualAPIKey, Header()]
    ):
        return await key_handler(request, headers.Authorization, inner)

    return auth_func


IndividualJwtAuth = Annotated[dict, Depends(individual_jwt_auth_factory(jwt_validator))]
