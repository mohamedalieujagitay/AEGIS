"""Account management (roadmap task 2.2): profile, password and sessions.

Every response here carries account or session information, so it is
``no-store``. Every state-changing request needs a CSRF token; the CSRF middleware
checks it before these handlers run. Ownership is enforced in the services: a
session or device that belongs to another account is reported as not found.

Each handler commits before it returns (see the note in ``auth.py``).
"""

import uuid
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response

from app.api.cookies import NO_STORE, clear_cookie, issue_csrf, set_cookie
from app.api.dependencies import Auth, CurrentUser, DbSession, client_ip, current_session
from app.core import clock
from app.core.errors import AppError
from app.core.security_log import security_event
from app.models.session import UserSession
from app.models.user import User
from app.schemas.account import (
    ActiveSessionResponse,
    ChangePasswordRequest,
    PasswordChangedResponse,
    ProfileResponse,
    RevokedSessionsResponse,
    UpdateProfileRequest,
)
from app.schemas.errors import ErrorResponse
from app.services import accounts, sessions, trusted_devices

router = APIRouter(prefix="/account", tags=["account"])

CurrentSessionDep = Annotated[tuple[UserSession, User], Depends(current_session)]


class SessionNotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "session_not_found"
    message = "No active session with this identifier."


def _errors(*statuses: int) -> dict[int | str, dict[str, object]]:
    return {status: {"model": ErrorResponse} for status in statuses}


def _profile(user: User) -> ProfileResponse:
    return ProfileResponse(
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        is_active=user.is_active,
    )


@router.get(
    "/profile",
    response_model=ProfileResponse,
    responses=_errors(401),
    summary="Your profile",
)
def get_profile(user: CurrentUser, response: Response) -> ProfileResponse:
    response.headers["Cache-Control"] = NO_STORE
    return _profile(user)


@router.patch(
    "/profile",
    response_model=ProfileResponse,
    responses=_errors(400, 401, 409, 422, 429, 503),
    summary="Change your username (requires your current password)",
)
def update_profile(
    payload: UpdateProfileRequest,
    response: Response,
    current: CurrentSessionDep,
    db: DbSession,
    auth: Auth,
) -> ProfileResponse:
    _, user = current
    auth.limiter.hit_sensitive_change(str(user.id))
    accounts.change_username(db, user, payload.username, payload.current_password)
    db.commit()
    response.headers["Cache-Control"] = NO_STORE
    return _profile(user)


@router.post(
    "/password",
    response_model=PasswordChangedResponse,
    responses=_errors(400, 401, 403, 422, 429, 503),
    summary="Change your password",
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    current: CurrentSessionDep,
    db: DbSession,
    auth: Auth,
) -> PasswordChangedResponse:
    """Change the password, sign out every other session and every trusted device.

    The current browser stays signed in: its session token is rotated, so the
    token it held before the change no longer works.
    """
    session, user = current
    now = clock.utcnow()
    auth.limiter.hit_sensitive_change(str(user.id))
    device = trusted_devices.find_valid(
        db, request.cookies.get(auth.settings.device_cookie_name), user, now
    )
    accounts.change_password(db, user, payload.current_password, payload.new_password, now)
    other_sessions = sessions.revoke_all_sessions(
        db, user.id, "password_changed", now, keep_session_id=session.id
    )
    token = sessions.rotate_token(db, session, now)
    if device is not None:
        # The browser's own trusted device was revoked with the password (D-070).
        clear_cookie(response, auth.settings.device_cookie_name, auth.settings)
    set_cookie(response, auth.settings.session_cookie_name, token, auth.settings)
    csrf_token = issue_csrf(response, auth.settings, auth.secret, token)
    security_event(
        "auth.password_changed",
        "Password changed",
        user_id=str(user.id),
        other_sessions_revoked=other_sessions,
        client_ip=client_ip(request),
    )
    db.commit()
    response.headers["Cache-Control"] = NO_STORE
    return PasswordChangedResponse(csrf_token=csrf_token)


@router.get(
    "/sessions",
    response_model=list[ActiveSessionResponse],
    responses=_errors(401),
    summary="Your active sessions",
)
def list_sessions(
    response: Response, current: CurrentSessionDep, db: DbSession, auth: Auth
) -> list[ActiveSessionResponse]:
    """Active sessions of the signed-in user only. No token, hash or address is returned."""
    session, user = current
    rows = sessions.list_active_sessions(db, user.id, auth.policy, clock.utcnow())
    response.headers["Cache-Control"] = NO_STORE
    return [
        ActiveSessionResponse(
            id=row.id,
            created_at=row.created_at,
            last_seen_at=row.last_seen_at,
            expires_at=row.expires_at,
            user_agent=row.user_agent,
            current=row.id == session.id,
        )
        for row in rows
    ]


@router.delete(
    "/sessions/{session_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses=_errors(401, 404),
    summary="Sign out one of your sessions",
)
def revoke_session(
    session_id: Annotated[uuid.UUID, Path()],
    request: Request,
    response: Response,
    current: CurrentSessionDep,
    db: DbSession,
    auth: Auth,
) -> Response:
    """Revoke one session. Revoking the current session signs this browser out, as logout does."""
    session, user = current
    revoked = sessions.revoke_owned_session(
        db, user.id, session_id, "revoked_by_user", clock.utcnow()
    )
    if revoked is None:
        raise SessionNotFoundError()
    is_current = revoked.id == session.id
    if is_current:
        clear_cookie(response, auth.settings.session_cookie_name, auth.settings)
        clear_cookie(response, auth.settings.csrf_cookie_name, auth.settings)
    security_event(
        "auth.logout" if is_current else "auth.session_revoked",
        "Signed out" if is_current else "Session revoked",
        user_id=str(user.id),
        client_ip=client_ip(request),
    )
    db.commit()
    response.status_code = HTTPStatus.NO_CONTENT
    return response


@router.post(
    "/sessions/revoke-others",
    response_model=RevokedSessionsResponse,
    responses=_errors(401, 403),
    summary="Sign out every session except this one",
)
def revoke_other_sessions(
    request: Request,
    response: Response,
    current: CurrentSessionDep,
    db: DbSession,
) -> RevokedSessionsResponse:
    """Trusted devices are not affected: only sessions end here (D-070)."""
    session, user = current
    revoked = sessions.revoke_all_sessions(
        db, user.id, "revoked_by_user", clock.utcnow(), keep_session_id=session.id
    )
    security_event(
        "auth.sessions_revoked",
        "Other sessions revoked",
        user_id=str(user.id),
        count=revoked,
        client_ip=client_ip(request),
    )
    db.commit()
    response.headers["Cache-Control"] = NO_STORE
    return RevokedSessionsResponse(revoked=revoked)
