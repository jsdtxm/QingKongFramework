from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from tortoise.exceptions import DoesNotExist, IntegrityError, ValidationError

if TYPE_CHECKING:
    from fastapi import Request


def add_tortoise_exception_handler(app):
    @app.exception_handler(DoesNotExist)
    async def doesnotexist_exception_handler(request: "Request", exc: DoesNotExist):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(IntegrityError)
    async def integrityerror_exception_handler(request: "Request", exc: IntegrityError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": [{"loc": [], "msg": str(exc), "type": "IntegrityError"}]
            },
        )

    @app.exception_handler(ValidationError)
    async def validationError_exception_handler(request: "Request", exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": [{"loc": [], "msg": str(exc), "type": "ValidationError"}]
            },
        )