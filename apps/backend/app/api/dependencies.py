"""Shared API dependencies: the authentication context and the signed-in user."""

import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import Settings
from app.core.errors import AppError
from app.core.security_log import security_event
from app.database.session import get_db_session
from app.models.session import UserSession
from app.models.user import User
from app.services.rate_limit import AuthRateLimiter
from app.services.sessions import SessionExpiredError, SessionPolicy, resolve_session


@dataclass(frozen=True)
class AuthContext:
    """Authentication configuration, created once per application."""

    settings: Settings
    secret: bytes
    policy: SessionPolicy
    limiter: AuthRateLimiter


class ForbiddenError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "forbidden"
    message = "You do not have permission to perform this action."


def get_auth(request: Request) -> AuthContext:
    auth: AuthContext = request.app.state.auth
    return auth


def client_ip(request: Request) -> str:
    """The client address, as determined by Uvicorn's trusted-proxy handling."""
    return request.client.host if request.client else "unknown"


DbSession = Annotated[Session, Depends(get_db_session)]
Auth = Annotated[AuthContext, Depends(get_auth)]


def current_session(request: Request, db: DbSession, auth: Auth) -> tuple[UserSession, User]:
    """The valid session of the request.

    Raises 401 ``authentication_required`` or ``session_expired``.
    """
    token = request.cookies.get(auth.settings.session_cookie_name)
    try:
        return resolve_session(db, token, auth.policy, clock.utcnow())
    except SessionExpiredError:
        security_event(
            "auth.session_expired",
            "Expired session refused",
            level=logging.INFO,
            client_ip=client_ip(request),
        )
        raise


def current_user(session: Annotated[tuple[UserSession, User], Depends(current_session)]) -> User:
    return session[1]


CurrentUser = Annotated[User, Depends(current_user)]


def require_instance_admin(request: Request, user: CurrentUser) -> User:
    """The signed-in user, who must be an instance administrator (FR-AUTH-006)."""
    if not user.is_instance_admin:
        security_event(
            "auth.forbidden",
            "Instance administration refused",
            level=logging.WARNING,
            user_id=str(user.id),
            path=request.url.path,
        )
        raise ForbiddenError()
    return user


InstanceAdmin = Annotated[User, Depends(require_instance_admin)]
