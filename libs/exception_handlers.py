import json
from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError as PydanticValidationError
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
    async def validationError_exception_handler(
        request: "Request", exc: ValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={
                "detail": [{"loc": [], "msg": str(exc), "type": "ValidationError"}]
            },
        )


def add_pydantic_validation_exception_handler(app):
    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_exception_handler(
        request: "Request", exc: PydanticValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={
                "detail": json.loads(exc.json(include_url=False, include_input=False))
            },
        )


def add_valueerror_exception_handler(app):
    @app.exception_handler(ValueError)
    async def valueerror_exception_handler(request: "Request", exc: ValueError):
        return JSONResponse(
            status_code=422,
            content={"detail": [{"loc": [], "msg": str(exc), "type": "ValueError"}]},
        )
