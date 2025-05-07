from typing import Union

from starlette.requests import Request
from starlette.websockets import WebSocket


def get_client_ip(request: Union[Request, WebSocket]):
    forwarded = request.headers.get("X-Forwarded-For")

    return forwarded.split(",")[0] if forwarded else request.client.host
