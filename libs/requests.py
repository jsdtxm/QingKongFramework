from fastapi.requests import Request as Request  # noqa
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from libs.contrib.auth.typing import UserProtocol


class DjangoStyleRequest(Request):
    """keep no additional data"""

    @property
    def GET(self):
        return self.query_params

    @property
    def POST(self):
        return self.form()

    @property
    def user(self) -> Optional[UserProtocol]:
        return None
