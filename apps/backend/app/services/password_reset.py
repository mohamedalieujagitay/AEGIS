"""Administrator and CLI password reset (PRD FR-AUTH-005, DECISIONS.md D-012, D-068).

There is no self-service "forgot password" flow and no email in v0.1.0:

- The instance administrator issues a reset token in the application. It is
  shown once, as a link, and handed to the user out of band. The user sets
  a new password with it. Tokens are 256-bit, single-use, expire after
  ``AEGIS_PASSWORD_RESET_TOKEN_TTL_MINUTES`` and are stored only as hashes.
  Issuing a new token invalidates the user's earlier unused tokens.
- The CLI (``python -m app.cli reset-password``) sets a new password
  directly, after prompting for it.

A completed reset revokes all of the user's sessions. Tokens and passwords
are never logged.
"""

import logging
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import NoReturn

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_token, new_token
from app.core.security_log import security_event
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services.accounts import set_password
from app.services.sessions import RETENTION, revoke_all_sessions


class InvalidResetTokenError(AppError):
    status_code = HTTPStatus.BAD_REQUEST
    code = "invalid_reset_token"
    message = "This reset link is invalid or has expired. Ask your administrator for a new one."


def issue_reset_token(
    db: Session,
    user: User,
    *,
    issued_by: User | None,
    method: str,
    ttl: timedelta,
    now: datetime,
) -> tuple[str, datetime]:
    """Create a reset token for ``user``; return the token (shown once) and its expiry."""
    db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
        )
    )
    token = new_token()
    expires_at = now + ttl
    db.add(
        PasswordResetToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=hash_token(token),
            issued_by_user_id=issued_by.id if issued_by else None,
            issue_method=method,
            created_at=now,
            expires_at=expires_at,
        )
    )
    db.flush()
    security_event(
        "auth.password_reset_issued",
        "Password reset token issued",
        user_id=str(user.id),
        actor_id=str(issued_by.id) if issued_by else None,
        method=method,
    )
    return token, expires_at


def redeem_reset_token(db: Session, token: str, new_password: str, now: datetime) -> User:
    """Set a new password with a reset token. The token is consumed only on success."""
    row = db.execute(
        select(PasswordResetToken, User)
        .join(User, User.id == PasswordResetToken.user_id)
        .where(PasswordResetToken.token_hash == hash_token(token))
        .with_for_update(of=PasswordResetToken)
    ).one_or_none()
    if row is None:
        _failed("unknown_token")
    reset, user = row
    if reset.used_at is not None:
        _failed("used_token", user)
    if now >= reset.expires_at:
        _failed("expired_token", user)
    if not user.is_active:
        _failed("inactive_account", user)
    set_password(db, user, new_password, now)
    reset.used_at = now
    revoked = revoke_all_sessions(db, user.id, "password_reset", now)
    security_event(
        "auth.password_reset_completed",
        "Password reset completed",
        user_id=str(user.id),
        method=reset.issue_method,
        revoked_count=revoked,
    )
    return user


def reset_password_directly(
    db: Session, user: User, new_password: str, now: datetime, *, operator: str
) -> int:
    """CLI reset: set the password and revoke all sessions. Returns sessions revoked.

    ``operator`` is the name of the operating-system account that ran the
    command, as the operating system reports it. It is not verified: anyone
    with shell access to the server can run the command. No account is
    created for the operator (PRD FR-AUTH-005; DECISIONS.md D-072).
    """
    set_password(db, user, new_password, now)
    revoked = revoke_all_sessions(db, user.id, "password_reset", now)
    security_event(
        "auth.password_reset_completed",
        "Password reset completed",
        user_id=str(user.id),
        method="cli",
        operator=operator,
        revoked_count=revoked,
    )
    return revoked


def purge_ended_reset_tokens(db: Session, now: datetime) -> int:
    """Delete reset tokens that were used or expired more than the retention period ago."""
    cutoff = now - RETENTION
    result = db.execute(
        delete(PasswordResetToken).where(
            or_(PasswordResetToken.used_at < cutoff, PasswordResetToken.expires_at < cutoff)
        )
    )
    return int(result.rowcount)  # type: ignore[attr-defined]


def _failed(reason: str, user: User | None = None) -> NoReturn:
    security_event(
        "auth.password_reset_failed",
        "Password reset refused",
        level=logging.WARNING,
        reason=reason,
        user_id=str(user.id) if user else None,
    )
    raise InvalidResetTokenError()
