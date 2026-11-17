"""Authentication endpoints (roadmap 2.1, DECISIONS.md D-061 to D-068).

Cookies (``__Host-`` prefix when ``AEGIS_COOKIE_SECURE``, the default):

- ``__Host-aegis_session``: the session token. HttpOnly, Secure,
  ``SameSite=Strict``, ``Path=/``, no ``Domain``, no ``Max-Age`` (it ends
  with the browser session; the server enforces the real expiry).
- ``__Host-aegis_csrf``: the CSRF token, same attributes. The token is also
  returned in the response body, for the ``X-CSRF-Token`` header.

No endpoint returns a session token in its body, and none are logged.
"""

import logging
import uuid
from datetime import timedelta
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path, Request, Response

from app.api.dependencies import Auth, CurrentUser, DbSession, client_ip
from app.core import clock
from app.core.config import Settings
from app.core.csrf import csrf_binding, issue_csrf_token
from app.core.errors import AppError
from app.core.security_log import security_event
from app.models.trusted_device import TrustedDevice
from app.models.user import User
from app.schemas.auth import (
    AuthOptionsResponse,
    CsrfResponse,
    LoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    SessionResponse,
    TrustedDeviceResponse,
    UserResponse,
)
from app.schemas.errors import ErrorResponse
from app.services import accounts, password_reset, sessions, trusted_devices
from app.services.rate_limit import Outcome

SECONDS_PER_DAY = 86400

router = APIRouter(prefix="/auth", tags=["authentication"])

NO_STORE = "no-store"


def _errors(*statuses: int) -> dict[int | str, dict[str, object]]:
    return {status: {"model": ErrorResponse} for status in statuses}


def _set_cookie(
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


def _clear_cookie(response: Response, name: str, settings: Settings) -> None:
    response.delete_cookie(
        name, path="/", httponly=True, secure=settings.cookie_secure, samesite="strict"
    )


def _issue_csrf(
    response: Response, auth_settings: Settings, secret: bytes, session_token: str | None
) -> str:
    token = issue_csrf_token(secret, csrf_binding(session_token), int(clock.utcnow().timestamp()))
    _set_cookie(response, auth_settings.csrf_cookie_name, token, auth_settings)
    return token


def _user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_instance_admin=user.is_instance_admin,
    )


def _start_session(
    request: Request, response: Response, db: DbSession, auth: Auth, user: User
) -> SessionResponse:
    """Create a new session (replacing any session cookie the browser sent) and rotate CSRF."""
    now = clock.utcnow()
    old_token = request.cookies.get(auth.settings.session_cookie_name)
    sessions.revoke_session_token(db, old_token, "replaced", now)
    sessions.purge_expired_sessions(db, now, user.id)
    token = sessions.create_session(
        db,
        user,
        auth.policy,
        now,
        client_ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    _set_cookie(response, auth.settings.session_cookie_name, token, auth.settings)
    csrf_token = _issue_csrf(response, auth.settings, auth.secret, token)
    response.headers["Cache-Control"] = NO_STORE
    return SessionResponse(user=_user(user), csrf_token=csrf_token)


@router.get("/csrf", response_model=CsrfResponse, summary="Get a CSRF token")
def csrf(request: Request, response: Response, auth: Auth) -> CsrfResponse:
    """Issue a CSRF token bound to the browser's session, or ``anonymous`` before sign-in."""
    session_token = request.cookies.get(auth.settings.session_cookie_name)
    response.headers["Cache-Control"] = NO_STORE
    return CsrfResponse(csrf_token=_issue_csrf(response, auth.settings, auth.secret, session_token))


@router.get("/options", response_model=AuthOptionsResponse, summary="Public sign-in options")
def options(db: DbSession, auth: Auth) -> AuthOptionsResponse:
    return AuthOptionsResponse(
        registration_enabled=accounts.registration_enabled(db),
        session_idle_timeout_minutes=auth.settings.session_idle_timeout_minutes,
        session_absolute_timeout_hours=auth.settings.session_absolute_timeout_hours,
    )


@router.post(
    "/register",
    response_model=SessionResponse,
    status_code=HTTPStatus.CREATED,
    responses=_errors(403, 409, 429, 503),
    summary="Create an account (when open registration is enabled)",
)
def register(
    payload: RegisterRequest, request: Request, response: Response, db: DbSession, auth: Auth
) -> SessionResponse:
    ip = client_ip(request)
    auth.limiter.hit_registration(ip)
    if not accounts.registration_enabled(db):
        raise accounts.RegistrationDisabledError()
    try:
        user = accounts.create_account(
            db, email=payload.email, username=payload.username, password=payload.password
        )
    except accounts.RegistrationRejectedError:
        security_event(
            "auth.registration_rejected",
            "Registration rejected",
            level=logging.WARNING,
            reason="duplicate",
            client_ip=ip,
        )
        raise
    security_event(
        "auth.registration_succeeded", "Account registered", user_id=str(user.id), client_ip=ip
    )
    session = _start_session(request, response, db, auth, user)
    # Commit before responding: the session dependency commits only after the
    # response is returned, so a request that follows this one could read the
    # previous state (found in the browser smoke test, 2026-11-17).
    db.commit()
    return session


@router.post(
    "/login",
    response_model=SessionResponse,
    responses=_errors(401, 429, 503),
    summary="Sign in",
)
def login(
    payload: LoginRequest, request: Request, response: Response, db: DbSession, auth: Auth
) -> SessionResponse:
    """Sign in. The attempt is reserved before the password is checked (D-070)."""
    ip = client_ip(request)
    now = clock.utcnow()
    known = accounts.find_user_by_email(db, payload.email)
    cookie_token = request.cookies.get(auth.settings.device_cookie_name)
    device = trusted_devices.find_valid(db, cookie_token, known, now) if known is not None else None
    attempt = auth.limiter.begin_login(payload.email, ip, trusted_device=device is not None)
    outcome: Outcome = "abandoned"
    try:
        user = accounts.authenticate(db, payload.email, payload.password, now)
        outcome = "success"
    except accounts.InvalidCredentialsError:
        outcome = "failure"
        raise
    finally:
        auth.limiter.finish_login(attempt, outcome)
    security_event("auth.login_succeeded", "Signed in", user_id=str(user.id), client_ip=ip)
    session = _start_session(request, response, db, auth, user)
    if device is not None:
        # The browser is already trusted: keep its device and its cookie (D-070).
        trusted_devices.mark_used(device, now)
    else:
        token = trusted_devices.issue(
            db,
            user,
            now=now,
            lifetime=timedelta(days=auth.settings.device_trust_days),
            user_agent=request.headers.get("user-agent"),
        )
        _set_cookie(
            response,
            auth.settings.device_cookie_name,
            token,
            auth.settings,
            max_age=auth.settings.device_trust_days * SECONDS_PER_DAY,
        )
    # Commit before responding: the session dependency commits only after the
    # response is returned, so a request that follows this one could read the
    # previous state (found in the browser smoke test, 2026-11-17).
    db.commit()
    return session


class DeviceNotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "device_not_found"
    message = "No trusted device with this identifier."


def _current_device(
    request: Request, db: DbSession, auth: Auth, user: User
) -> TrustedDevice | None:
    now = clock.utcnow()
    return trusted_devices.find_valid(
        db, request.cookies.get(auth.settings.device_cookie_name), user, now
    )


@router.get(
    "/devices",
    response_model=list[TrustedDeviceResponse],
    responses=_errors(401),
    summary="Browsers trusted for sign-in",
)
def list_devices(
    request: Request, response: Response, user: CurrentUser, db: DbSession, auth: Auth
) -> list[TrustedDeviceResponse]:
    """The signed-in user's trusted devices. Metadata only: no token, no hash (D-070)."""
    now = clock.utcnow()
    current = _current_device(request, db, auth, user)
    response.headers["Cache-Control"] = NO_STORE
    return [
        TrustedDeviceResponse(
            id=device.id,
            created_at=device.created_at,
            expires_at=device.expires_at,
            last_used_at=device.last_used_at,
            user_agent=device.user_agent,
            current=current is not None and current.id == device.id,
        )
        for device in trusted_devices.list_for_user(db, user.id, now)
    ]


@router.delete(
    "/devices/{device_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses=_errors(401, 404),
    summary="Revoke one of your trusted browsers",
)
def revoke_device(
    device_id: Annotated[uuid.UUID, Path()],
    request: Request,
    response: Response,
    user: CurrentUser,
    db: DbSession,
    auth: Auth,
) -> Response:
    """Revoke one of your devices. Another account's device is reported as not found."""
    now = clock.utcnow()
    current = _current_device(request, db, auth, user)
    if not trusted_devices.revoke(db, user.id, device_id, "revoked_by_user", now):
        raise DeviceNotFoundError()
    if current is not None and current.id == device_id:
        _clear_cookie(response, auth.settings.device_cookie_name, auth.settings)
    db.commit()
    response.status_code = HTTPStatus.NO_CONTENT
    return response


@router.post("/logout", status_code=HTTPStatus.NO_CONTENT, summary="Sign out")
def logout(request: Request, response: Response, db: DbSession, auth: Auth) -> Response:
    """Revoke the session server-side and clear the cookies. Succeeds even if already signed out."""
    token = request.cookies.get(auth.settings.session_cookie_name)
    if sessions.revoke_session_token(db, token, "logout", clock.utcnow()):
        security_event("auth.logout", "Signed out", client_ip=client_ip(request))
    response.status_code = HTTPStatus.NO_CONTENT
    _clear_cookie(response, auth.settings.session_cookie_name, auth.settings)
    _clear_cookie(response, auth.settings.csrf_cookie_name, auth.settings)
    # Commit before responding: the session dependency commits only after the
    # response is returned, so a request that follows this one could read the
    # previous state (found in the browser smoke test, 2026-11-17).
    db.commit()
    return response


@router.get(
    "/me", response_model=UserResponse, responses=_errors(401), summary="The signed-in user"
)
def me(user: CurrentUser, response: Response) -> UserResponse:
    response.headers["Cache-Control"] = NO_STORE
    return _user(user)


@router.post(
    "/password/reset",
    status_code=HTTPStatus.NO_CONTENT,
    responses=_errors(400, 422, 429, 503),
    summary="Set a new password with a reset token issued by the administrator",
)
def reset_password(
    payload: PasswordResetRequest, request: Request, response: Response, db: DbSession, auth: Auth
) -> Response:
    auth.limiter.hit_password_reset(client_ip(request))
    password_reset.redeem_reset_token(db, payload.token, payload.new_password, clock.utcnow())
    response.status_code = HTTPStatus.NO_CONTENT
    _clear_cookie(response, auth.settings.session_cookie_name, auth.settings)
    _clear_cookie(response, auth.settings.csrf_cookie_name, auth.settings)
    _clear_cookie(response, auth.settings.device_cookie_name, auth.settings)
    # Commit before responding: the session dependency commits only after the
    # response is returned, so a request that follows this one could read the
    # previous state (found in the browser smoke test, 2026-11-17).
    db.commit()
    return response
