from typing import TYPE_CHECKING

from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import websocket_request_validation_exception_handler
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.utils import is_body_allowed_for_status_code
from pydantic import ValidationError as PydanticValidationError
from starlette import status
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response
from tortoise.exceptions import DoesNotExist, OperationalError
from tortoise.exceptions import ValidationError as TortoiseValidationError

if TYPE_CHECKING:
    from fastapi import Request


async def http_exception_handler(request: "Request", exc: HTTPException) -> Response:
    headers = getattr(exc, "headers", None)
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=headers)
    return JSONResponse(
        {
            "error": exc.__class__.__name__,
            "message": exc.detail,
            "detail": exc.detail,
        },
        status_code=exc.status_code,
        headers=headers,
    )


async def request_validation_exception_handler(
    request: "Request", exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": exc.__class__.__name__,
            "message": "Invalid request data",
            "detail": jsonable_encoder(exc.errors()),
        },
    )


async def tortoise_operation_exception_handler(
    request: "Request", exc: OperationalError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "detail": str(exc),
        },
    )


async def tortoise_doesnotexist_exception_handler(
    request: "Request", exc: DoesNotExist
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "detail": str(exc),
        },
    )


async def tortoise_validation_exception_handler(
    request: "Request", exc: TortoiseValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "detail": str(exc),
        },
    )


async def pydantic_validation_exception_handler(
    request: "Request", exc: PydanticValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": exc.__class__.__name__,
            "message": "Invalid request data",
            "detail": jsonable_encoder(
                exc.errors(include_url=False, include_input=False)
            ),
        },
    )


async def valueerror_exception_handler(
    request: "Request", exc: ValueError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "detail": str(exc),
        },
    )


async def permission_error_exception_handler(
    request: "Request", exc: PermissionError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "detail": str(exc),
        },
    )


def get_default_exception_handlers():
    return {
        HTTPException: http_exception_handler,
        RequestValidationError: request_validation_exception_handler,
        WebSocketRequestValidationError: websocket_request_validation_exception_handler,
        OperationalError: tortoise_operation_exception_handler,
        DoesNotExist: tortoise_doesnotexist_exception_handler,
        TortoiseValidationError: tortoise_validation_exception_handler,
        PydanticValidationError: pydantic_validation_exception_handler,
        ValueError: valueerror_exception_handler,
        PermissionError: permission_error_exception_handler,
    }
