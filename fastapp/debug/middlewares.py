from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class DebugBodyCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        form = await request.form()

        request.state.cache_body = body
        request.state.cache_form = form

        response = await call_next(request)
        return response
