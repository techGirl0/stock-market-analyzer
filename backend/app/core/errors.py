from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.v1 import ErrorDetail, ErrorResponse


class BackendError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", request.headers.get("X-Request-ID"))


def error_body(code: str, message: str, request_id: str | None, details: Any = None) -> dict:
    """The one place the API's error envelope is shaped."""
    return ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id,
            details=details if isinstance(details, dict) else {},
        )
    ).model_dump()


def backend_error_handler(request: Request, exc: BackendError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, _request_id(request), exc.details),
    )


def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body(
            "validation_error",
            "The request was not valid.",
            _request_id(request),
            {"fields": exc.errors()},
        ),
    )


def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_body(
            "internal_error",
            "An unexpected server error occurred.",
            _request_id(request),
        ),
    )
