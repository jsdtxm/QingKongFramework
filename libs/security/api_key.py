from typing import Annotated, Any, Callable

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.security.base import SecurityBase
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

key_auth_header = APIKeyHeader(name="Authorization", auto_error=False)


def plain_validator(request: Request, key: str) -> bool:  # pylint: disable=W0613
    """plain_validator"""

    return key == "let_me_in"


def api_key_auth_factory(
    inner: Callable[[Request, str], bool] = None, dependency: SecurityBase = None
):
    inner = inner or plain_validator
    dependency = dependency or key_auth_header

    async def auth_func(request: Request, key: str = Security(dependency)):
        if not key:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"Authenticate": "Bearer"},
            )
        try:
            return inner(request, key)
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Invalid API key provided."
            )

    return auth_func


ApiKeyAuth = Annotated[Any, Depends(api_key_auth_factory())]
