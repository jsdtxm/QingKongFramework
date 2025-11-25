from starlette.datastructures import URL, Headers
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware as StarletteTrustedHostMiddleware,
)
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.types import Receive, Scope, Send


class TrustedHostMiddleware(StarletteTrustedHostMiddleware):
    def __init__(self, *args, allow_local_client: bool = True, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.allow_local_client = allow_local_client

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.allow_any or scope["type"] not in (
            "http",
            "websocket",
        ):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        if self.allow_local_client:
            client_host, _ = scope.get("client", ("", 0))
            if client_host == "127.0.0.1":
                await self.app(scope, receive, send)
                return

        headers = Headers(scope=scope)
        host = headers.get("host", "").split(":")[0]
        is_valid_host = False
        found_www_redirect = False
        for pattern in self.allowed_hosts:
            if host == pattern or (
                pattern.startswith("*") and host.endswith(pattern[1:])
            ):
                is_valid_host = True
                break
            elif "www." + host == pattern:
                found_www_redirect = True

        if is_valid_host:
            await self.app(scope, receive, send)
            return
        else:
            response: Response
            if found_www_redirect and self.www_redirect:
                url = URL(scope=scope)
                redirect_url = url.replace(netloc="www." + url.netloc)
                response = RedirectResponse(url=str(redirect_url))
            else:
                response = JSONResponse(
                    {"message": "Invalid host header"}, status_code=400
                )
            await response(scope, receive, send)
            return
