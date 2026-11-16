"""Per-request context: request IDs and request logging.

Every request gets an ID, returned in the ``X-Request-ID`` response header
and attached to every log record written while the request is handled. A
client-supplied ID is reused only if it is short and contains only safe
characters, so it cannot be used to inject content into logs.

Each request is logged once, without its query string or body, because
those can carry secrets (for example tokens in URLs).

Routine health probes are logged at DEBUG instead of INFO, so container and
orchestrator checks every few seconds do not flood the logs (DECISIONS.md
D-060). A handler opts in by calling ``mark_routine_probe`` just before it
returns a normal result; requests that fail with an unexpected error are
never marked and keep their ERROR level.
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

ROUTINE_PROBE_STATE = "routine_probe"
"""Request state flag set by health endpoints for their normal results."""

ROUTINE_PROBE_STATUSES = frozenset({200, 503})
"""Statuses a marked probe may return and still be logged at DEBUG."""


def mark_routine_probe(state: object) -> None:
    """Mark the current request as a routine health probe (logged at DEBUG).

    ``state`` is ``request.state``; Starlette stores its attributes in the
    request scope, where the middleware reads them after the response.
    """
    setattr(state, ROUTINE_PROBE_STATE, True)


def _log_level(scope: Scope, status_code: int) -> int:
    state = scope.get("state", {})
    if state.get(ROUTINE_PROBE_STATE) is True and status_code in ROUTINE_PROBE_STATUSES:
        return logging.DEBUG
    return logging.ERROR if status_code >= 500 else logging.INFO


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
                _log_level(scope, status_code),
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
