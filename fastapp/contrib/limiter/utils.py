from typing import Union

from starlette.requests import Request
from starlette.websockets import WebSocket

from fastapp.utils.ip import get_client_ip


async def ip_identifier(request: Union[Request, WebSocket]):
    """
    Generate a unique identifier based on the client's IP address and the request path.

    Args:
        request (Union[Request, WebSocket]): The incoming request or WebSocket object.

    Returns:
        str: A string containing the client's IP address and the request path, separated by a colon.
    """
    ip = get_client_ip(request)
    return ip + ":" + request.scope["path"]
