import http
from typing import Optional

from starlette import status
from starlette.exceptions import HTTPException
from tortoise.exceptions import DoesNotExist as DoesNotExist  # noqa
from tortoise.exceptions import IntegrityError as IntegrityError  # noqa
from tortoise.exceptions import ValidationError as ValidationError  # noqa

ObjectDoesNotExist = DoesNotExist


class ImproperlyConfigured(Exception):
    """Django is somehow improperly configured"""

    pass


class HttpCodeException(HTTPException):
    status_code = 500

    def __init__(
        self,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
        code: Optional[int] = None,
    ) -> None:
        self.status_code = code or self.status_code
        if detail is None:
            detail = http.HTTPStatus(self.status_code).phrase
        self.detail = detail
        self.headers = headers


class NotAuthenticated(HttpCodeException):
    """The user did not have permission to do that"""

    status_code = status.HTTP_401_UNAUTHORIZED


class PermissionDenied(HttpCodeException):
    """The user did not have permission to do that"""

    status_code = status.HTTP_403_FORBIDDEN


class Http404(HttpCodeException):
    status_code = status.HTTP_404_NOT_FOUND


class MethodNotAllowed(HttpCodeException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
