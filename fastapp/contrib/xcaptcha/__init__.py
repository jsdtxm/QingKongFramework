from typing import Callable, Optional

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from fastapp.contrib.limiter.utils import ip_identifier
from fastapp.contrib.xcaptcha.exceptions import ThrottledException


async def http_default_callback(
    request: Request, response: Response, exception: ThrottledException
):
    """
    default callback when too many requests
    :param request:
    :param pexpire: The remaining milliseconds
    :param response:
    :return:
    """

    raise HTTPException(
        HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "action": exception.action,
            "message": exception.message,
            "track_id": exception.track_id,
        },
    )


class XCaptchaLimiter:
    http_callback: Optional[Callable] = None

    @classmethod
    async def init(
        cls,
        identifier: Callable = ip_identifier,
        http_callback: Callable = http_default_callback,
    ) -> None:
        cls.identifier = identifier
        cls.http_callback = http_callback
