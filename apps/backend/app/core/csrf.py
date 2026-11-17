"""CSRF protection: signed double-submit tokens (DECISIONS.md D-065).

Every state-changing request (POST, PUT, PATCH, DELETE) under ``/api/`` must
pass all of these checks, or it is refused with 403 ``csrf_failed``:

1. **Origin.** If the browser sends an ``Origin`` header, it must be the
   request's own origin or one of ``AEGIS_ALLOWED_ORIGINS``. ``Origin: null``
   and ``Sec-Fetch-Site: cross-site`` are refused.
2. **Double submit.** The ``X-CSRF-Token`` header must equal the CSRF cookie.
   Another site can make the browser send the cookie, but cannot read it
   (HttpOnly, ``SameSite=Strict``) or set it (``__Host-`` prefix), so it
   cannot put the same value in the header.
3. **Signature and binding.** The token is
   ``v1.<issued-at>.<nonce>.<HMAC-SHA-256(secret, "v1.<issued-at>.<nonce>|<binding>")>``.
   The binding is what the token belongs to:

   - before sign-in (no session cookie): ``anonymous``;
   - after sign-in: ``session:<SHA-256 of the session cookie>``.

   A token is accepted only with the binding of the request it arrives
   with, so a token from one session is useless with another session, and
   an anonymous token stops working as soon as a session exists.
4. **Age.** Tokens older than the absolute session lifetime are refused.

Rotation: sign-in and registration return a new token bound to the new
session; sign-out and password reset clear the CSRF cookie, and the client
fetches a new anonymous token from ``GET /api/v1/auth/csrf``.

Protection is deny-by-default: new endpoints are covered automatically.
``SameSite=Strict`` on both cookies is an additional layer, not the only one.
"""

import base64
import hashlib
import hmac
import logging
import secrets
from typing import Final

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core import clock
from app.core.errors import error_response
from app.core.security_log import security_event

CSRF_HEADER: Final = "X-CSRF-Token"
TOKEN_VERSION: Final = "v1"  # noqa: S105 (token format version, not a secret)
UNSAFE_METHODS: Final = frozenset({"POST", "PUT", "PATCH", "DELETE"})
ANONYMOUS_BINDING: Final = "anonymous"


def csrf_binding(session_cookie: str | None) -> str:
    """The binding for a request: its session, or ``anonymous`` before sign-in."""
    if not session_cookie:
        return ANONYMOUS_BINDING
    return "session:" + hashlib.sha256(session_cookie.encode("utf-8")).hexdigest()


def _signature(secret: bytes, payload: str, binding: str) -> str:
    digest = hmac.new(secret, f"{payload}|{binding}".encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def issue_csrf_token(secret: bytes, binding: str, now: int) -> str:
    """A new token for ``binding``, issued at Unix time ``now``."""
    payload = f"{TOKEN_VERSION}.{now}.{secrets.token_urlsafe(16)}"
    return f"{payload}.{_signature(secret, payload, binding)}"


def verify_csrf_token(secret: bytes, token: str, binding: str, now: int, max_age: int) -> bool:
    parts = token.split(".")
    if len(parts) != 4 or parts[0] != TOKEN_VERSION or not parts[1].isdigit():
        return False
    issued_at = int(parts[1])
    if not 0 <= now - issued_at <= max_age:
        return False
    expected = _signature(secret, ".".join(parts[:3]), binding)
    return hmac.compare_digest(expected, parts[3])


class CsrfMiddleware:
    """Refuse state-changing API requests without valid CSRF proof."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        secret: bytes,
        session_cookie: str,
        csrf_cookie: str,
        allowed_origins: frozenset[str],
        max_age: int,
    ) -> None:
        self.app = app
        self._secret = secret
        self._session_cookie = session_cookie
        self._csrf_cookie = csrf_cookie
        self._allowed_origins = allowed_origins
        self._max_age = max_age

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] not in UNSAFE_METHODS
            or not scope["path"].startswith("/api/")
        ):
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        reason = self._rejection_reason(request)
        if reason is None:
            await self.app(scope, receive, send)
            return
        security_event(
            "auth.csrf_rejected",
            "Request refused by CSRF protection",
            level=logging.WARNING,
            reason=reason,
            method=scope["method"],
            path=scope["path"],
            client_ip=request.client.host if request.client else None,
        )
        response = error_response(
            request,
            403,
            "csrf_failed",
            "The request could not be verified. Reload the page and try again.",
        )
        await response(scope, receive, send)

    def _own_origin(self, request: Request) -> str | None:
        host = request.headers.get("host")
        return f"{request.url.scheme}://{host}" if host else None

    def _rejection_reason(self, request: Request) -> str | None:
        origin = request.headers.get("origin")
        if origin is not None:
            origin = origin.rstrip("/")
            if origin != self._own_origin(request) and origin not in self._allowed_origins:
                return "origin"
        if request.headers.get("sec-fetch-site") == "cross-site":
            return "cross_site"
        header = request.headers.get(CSRF_HEADER)
        cookie = request.cookies.get(self._csrf_cookie)
        if not header or not cookie:
            return "missing_token"
        if not hmac.compare_digest(header, cookie):
            return "token_mismatch"
        binding = csrf_binding(request.cookies.get(self._session_cookie))
        now = int(clock.utcnow().timestamp())
        if not verify_csrf_token(self._secret, header, binding, now, self._max_age):
            return "invalid_token"
        return None
