import http

from starlette.exceptions import HTTPException


class ImproperlyConfigured(Exception):
    """Django is somehow improperly configured"""

    pass


class PermissionDenied(Exception):
    """The user did not have permission to do that"""

    pass


class Http404(HTTPException):
    def __init__(
        self,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if detail is None:
            detail = http.HTTPStatus(404).phrase
        self.status_code = 404
        self.detail = detail
        self.headers = headers
