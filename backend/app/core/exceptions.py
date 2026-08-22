import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def _error_response(
    request: Request,
    code: str,
    message: str,
    details: Any = None,
    status_code: int = 400,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return _error_response(request, exc.code, exc.message, exc.details, exc.status_code)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        code = detail.get("code", "HTTP_ERROR")
        message = detail.get("message", "Request could not be completed.")
        details = detail.get("details")
    else:
        code = "HTTP_ERROR"
        message = str(detail)
        details = None
    return _error_response(request, code, message, details, exc.status_code)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details: dict[str, list[str]] = {}
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", []))
        details.setdefault(location, []).append(error.get("msg", "Invalid value"))
    return _error_response(request, "VALIDATION_ERROR", "Request validation failed.", details, 422)


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).exception("Unhandled application error", exc_info=exc)
    return _error_response(request, "INTERNAL_ERROR", "An unexpected error occurred.", None, 500)