"""Server-side session lifecycle (PRD FR-AUTH-003, DECISIONS.md D-064).

- A session token is 256 random bits, given to the browser once in an
  HttpOnly cookie. Only its SHA-256 hash is stored.
- Expiry is enforced here, on every request, whatever the browser sends:
  a session ends ``session_idle_timeout_minutes`` after its last use and
  ``session_absolute_timeout_hours`` after sign-in.
- ``last_seen_at`` is updated at most once a minute, to avoid a database
  write on every request.
- Revoked and expired sessions are kept for seven days, then purged.
"""

import ipaddress
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Final

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import hash_token, new_token
from app.models.session import UserSession
from app.models.user import User

LAST_SEEN_RESOLUTION: Final = timedelta(seconds=60)
RETENTION: Final = timedelta(days=7)
USER_AGENT_MAX_LENGTH: Final = 256


class AuthenticationRequiredError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "authentication_required"
    message = "Sign in to continue."


class SessionExpiredError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "session_expired"
    message = "Your session has expired. Sign in again."


@dataclass(frozen=True)
class SessionPolicy:
    idle_timeout: timedelta
    absolute_timeout: timedelta

    @classmethod
    def from_settings(cls, settings: Settings) -> "SessionPolicy":
        return cls(
            idle_timeout=timedelta(minutes=settings.session_idle_timeout_minutes),
            absolute_timeout=timedelta(hours=settings.session_absolute_timeout_hours),
        )


def _valid_ip(value: str | None) -> str | None:
    """``value`` if it is an IP address; otherwise None (for example a Unix socket peer)."""
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def create_session(
    db: Session,
    user: User,
    policy: SessionPolicy,
    now: datetime,
    *,
    client_ip: str | None,
    user_agent: str | None,
) -> str:
    """Create a session for ``user`` and return its token (shown to the browser only)."""
    token = new_token()
    db.add(
        UserSession(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=hash_token(token),
            created_at=now,
            last_seen_at=now,
            expires_at=now + policy.absolute_timeout,
            ip_address=_valid_ip(client_ip),
            user_agent=(user_agent or "")[:USER_AGENT_MAX_LENGTH] or None,
        )
    )
    db.flush()
    return token


def resolve_session(
    db: Session, token: str | None, policy: SessionPolicy, now: datetime
) -> tuple[UserSession, User]:
    """Return the valid session for ``token`` and its user, or raise a 401 error."""
    if not token:
        raise AuthenticationRequiredError()
    row = db.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(UserSession.token_hash == hash_token(token))
    ).one_or_none()
    if row is None:
        raise AuthenticationRequiredError()
    session, user = row
    if session.revoked_at is not None or not user.is_active:
        raise AuthenticationRequiredError()
    if now >= session.expires_at or now >= session.last_seen_at + policy.idle_timeout:
        raise SessionExpiredError()
    if now - session.last_seen_at >= LAST_SEEN_RESOLUTION:
        session.last_seen_at = now
    return session, user


def revoke_session_token(db: Session, token: str | None, reason: str, now: datetime) -> bool:
    """Revoke the session for ``token`` if it exists and is not already revoked."""
    if not token:
        return False
    result = db.execute(
        update(UserSession)
        .where(UserSession.token_hash == hash_token(token), UserSession.revoked_at.is_(None))
        .values(revoked_at=now, revoked_reason=reason)
    )
    return bool(result.rowcount)  # type: ignore[attr-defined]


def revoke_all_sessions(
    db: Session,
    user_id: uuid.UUID,
    reason: str,
    now: datetime,
    *,
    keep_session_id: uuid.UUID | None = None,
) -> int:
    """Revoke every session of a user (password reset, D-064). Returns the number revoked.

    ``keep_session_id`` leaves one session active (the browser making a password change).
    """
    statement = update(UserSession).where(
        UserSession.user_id == user_id, UserSession.revoked_at.is_(None)
    )
    if keep_session_id is not None:
        statement = statement.where(UserSession.id != keep_session_id)
    result = db.execute(statement.values(revoked_at=now, revoked_reason=reason))
    return int(result.rowcount)  # type: ignore[attr-defined]


def list_active_sessions(
    db: Session, user_id: uuid.UUID, policy: SessionPolicy, now: datetime
) -> list[UserSession]:
    """The user's sessions that could still be used: not revoked, not expired, not idle.

    Newest first. Only the account's own sessions are returned.
    """
    return list(
        db.scalars(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
                UserSession.last_seen_at > now - policy.idle_timeout,
            )
            .order_by(UserSession.created_at.desc())
        ).all()
    )


def revoke_owned_session(
    db: Session, user_id: uuid.UUID, session_id: uuid.UUID, reason: str, now: datetime
) -> UserSession | None:
    """Revoke one active session that belongs to ``user_id``.

    Returns the revoked session, or None when the session does not exist, is not
    active, or belongs to another account (the caller answers all three alike).
    """
    session = db.scalar(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
    )
    if session is None:
        return None
    session.revoked_at = now
    session.revoked_reason = reason
    return session


def rotate_token(db: Session, session: UserSession, now: datetime) -> str:
    """Give ``session`` a new token; the previous token stops working at once.

    Used after a password change, so a token held by someone else before the
    change cannot be used afterwards. The session itself (its id, expiry and
    device) is unchanged.
    """
    token = new_token()
    session.token_hash = hash_token(token)
    session.last_seen_at = now
    db.flush()
    return token


def purge_expired_sessions(db: Session, now: datetime, user_id: uuid.UUID | None = None) -> int:
    """Delete sessions that ended more than ``RETENTION`` ago."""
    cutoff = now - RETENTION
    statement = delete(UserSession).where(
        or_(UserSession.expires_at < cutoff, UserSession.revoked_at < cutoff)
    )
    if user_id is not None:
        statement = statement.where(UserSession.user_id == user_id)
    return int(db.execute(statement).rowcount)  # type: ignore[attr-defined]
