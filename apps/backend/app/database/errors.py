"""Safe API errors for database failures.

When the database cannot be reached (connection refused, timeout, pool
exhausted), clients receive a generic 503 ``database_unavailable``. Host
names, credentials, SQL and driver messages are never returned; the failure
is logged server-side without them.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app.core.errors import error_response
from app.database.config import DatabaseUnavailableError

logger = logging.getLogger("app.database")


async def _handle_database_unavailable(request: Request, exc: Exception) -> JSONResponse:
    # Only the exception type is logged: driver messages can include host
    # names and other connection details.
    logger.error(
        "Database unavailable",
        extra={
            "event": "database.unavailable",
            "error_type": type(exc).__name__,
            "request_id": getattr(request.state, "request_id", None),
        },
    )
    error = DatabaseUnavailableError()
    return error_response(request, HTTPStatus.SERVICE_UNAVAILABLE, error.code, error.message)


def register_database_exception_handlers(app: FastAPI) -> None:
    for exception_type in (OperationalError, InterfaceError, PoolTimeoutError):
        app.add_exception_handler(exception_type, _handle_database_unavailable)
