"""Per-request context: request IDs and request logging.

Every request gets an ID, returned in the ``X-Request-ID`` response header
and attached to every log record written while the request is handled. A
client-supplied ID is reused only if it is short and contains only safe
characters, so it cannot be used to inject content into logs.

Each request is logged once, without its query string or body, because
those can carry secrets (for example tokens in URLs).
"""

import logging
import re
import time
import uuid
from contextvars import ContextVar

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"

_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{8,64}")

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
"""Request ID of the request being handled in the current context, if any."""

logger = logging.getLogger("app.request")


def _resolve_request_id(scope: Scope) -> str:
    headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
    for name, value in headers:
        if name == b"x-request-id":
            candidate = value.decode("latin-1")
            if _SAFE_REQUEST_ID.fullmatch(candidate):
                return candidate
            break
    return uuid.uuid4().hex


class RequestContextMiddleware:
    """Assign a request ID, expose it to logs and handlers, and log the request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _resolve_request_id(scope)
        # Exception handlers run outside this middleware, after the context
        # variable is reset, so the ID is also stored in the request state.
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_var.set(request_id)
        status_code = 500
        started = time.perf_counter()

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.log(
                logging.ERROR if status_code >= 500 else logging.INFO,
                "%s %s %s",
                scope["method"],
                scope["path"],
                status_code,
                extra={
                    "event": "http.request",
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            request_id_var.reset(token)
