from starlette.exceptions import HTTPException


class ImproperlyConfigured(Exception):
    """Django is somehow improperly configured"""

    pass


class PermissionDenied(Exception):
    """The user did not have permission to do that"""

    pass
