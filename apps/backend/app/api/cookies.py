"""Session and CSRF cookies, and the no-store header, shared by the account routes.

Cookies are HttpOnly, SameSite=Strict, host-only (``__Host-`` names) and marked
Secure whenever the deployment is served over HTTPS (DECISIONS.md D-064, D-065).
"""

from fastapi import Response

from app.core import clock
from app.core.config import Settings
from app.core.csrf import csrf_binding, issue_csrf_token

NO_STORE = "no-store"
"""``Cache-Control`` value for responses that contain account or session information."""


def set_cookie(
    response: Response, name: str, value: str, settings: Settings, *, max_age: int | None = None
) -> None:
    response.set_cookie(
        name,
        value,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
        max_age=max_age,
    )


def clear_cookie(response: Response, name: str, settings: Settings) -> None:
    response.delete_cookie(
        name, path="/", httponly=True, secure=settings.cookie_secure, samesite="strict"
    )


def issue_csrf(
    response: Response, auth_settings: Settings, secret: bytes, session_token: str | None
) -> str:
    token = issue_csrf_token(secret, csrf_binding(session_token), int(clock.utcnow().timestamp()))
    set_cookie(response, auth_settings.csrf_cookie_name, token, auth_settings)
    return token
