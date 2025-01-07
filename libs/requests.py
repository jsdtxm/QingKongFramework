from fastapi.requests import Request as Request  # noqa
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from libs.contrib.auth.typing import UserProtocol


class DjangoStyleRequest:
    """keep no additional data"""
    
    def __init__(self, request: Request, user: Optional["UserProtocol"]=None):
        self.request = request
        self.user = user

        self._data = Empty

    @property
    def GET(self):
        return self.request.query_params

    @property
    def POST(self):
        return self.form()