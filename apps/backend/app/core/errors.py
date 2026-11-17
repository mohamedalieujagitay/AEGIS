"""Centralized exception handling.

Every error response has the same shape (``app.schemas.errors.ErrorResponse``)
and carries the request ID. Internal details such as exception messages,
tracebacks and submitted input values are never returned to the client;
unexpected exceptions are logged server-side with their traceback.

Note: when ``debug`` is enabled, Starlette returns its own traceback page
for unexpected exceptions instead of calling the handler. Debug mode is
rejected in production (``app.core.config.Settings``).
"""

import logging
from collections.abc import Mapping
from http import HTTPStatus
from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import REQUEST_ID_HEADER
from app.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger("app.errors")


class AppError(Exception):
    """Base class for expected application errors.

    Subclasses set a status code, a stable error code and a message that is
    safe to show to clients. Never put secrets or internal details in the
    message.
    """

    status_code: int = HTTPStatus.BAD_REQUEST
    code: str = "bad_request"
    message: str = "The request could not be processed."

    def __init__(
        self, message: str | None = None, headers: Mapping[str, str] | None = None
    ) -> None:
        if message is not None:
            self.message = message
        self.headers: dict[str, str] = dict(headers or {})
        """Extra response headers, for example ``Retry-After``."""
        super().__init__(self.message)


class RequestBodyTooLargeError(AppError):
    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    code = "request_too_large"
    message = "The request body is too large."


def _request_id(request: Request) -> str | None:
    value = getattr(request.state, "request_id", None)
    return value if isinstance(value, str) else None


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build an error response in the standard format."""
    request_id = _request_id(request)
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, request_id=request_id, details=details)
    )
    response_headers = dict(headers or {})
    if request_id is not None:
        response_headers[REQUEST_ID_HEADER] = request_id
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", exclude_none=True),
        headers=response_headers,
    )


def _status_code_name(status_code: int) -> tuple[str, str]:
    try:
        status = HTTPStatus(status_code)
    except ValueError:
        return "http_error", "The request could not be processed."
    return status.phrase.lower().replace(" ", "_").replace("-", "_"), f"{status.phrase}."


# FastAPI calls each handler below only for the exception type it is
# registered for (see ``register_exception_handlers``), so ``cast`` only
# narrows the declared ``Exception`` parameter for the type checker.


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    error = cast(AppError, exc)
    return error_response(
        request, error.status_code, error.code, error.message, headers=error.headers or None
    )


async def _handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    # Framework errors such as 404 and 405. The standard reason phrase is used
    # instead of the exception detail, which may contain developer text.
    error = cast(StarletteHTTPException, exc)
    code, message = _status_code_name(error.status_code)
    return error_response(request, error.status_code, code, message, headers=error.headers)


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    # Only the location, message and type of each error are returned. The
    # submitted input and validation context are dropped, because they can
    # contain sensitive values such as passwords.
    error_list = cast(RequestValidationError, exc).errors()
    details = [
        ErrorDetail(
            location=[part for part in error.get("loc", ()) if isinstance(part, str | int)],
            message=str(error.get("msg", "Invalid value.")),
            type=str(error.get("type", "value_error")),
        )
        for error in error_list
    ]
    return error_response(
        request,
        HTTPStatus.UNPROCESSABLE_ENTITY,
        "validation_error",
        "The request is invalid.",
        details=details,
    )


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # This handler runs after the request context has ended, so the request
    # ID is passed explicitly for correlation with the client's response.
    logger.error(
        "Unhandled exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "event": "error.unhandled",
            "path": request.url.path,
            "request_id": _request_id(request),
        },
    )
    return error_response(
        request,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "internal_error",
        "An unexpected error occurred.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install the standard error handlers on the application."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
