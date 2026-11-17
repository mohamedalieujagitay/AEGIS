"""Trusted-device records (DECISIONS.md D-070).

Rules, enforced here and nowhere else:

- Only the SHA-256 hash of a device token is stored (``hash_token``).
- A device is valid only for its own account, when it is not revoked, not
  expired and the account is active. A token presented for another account is
  refused (replay across accounts).
- Lifetime is fixed at issue time and never extended by use, at most 30 days.
- A password change or reset, and an account deactivation, revoke every device
  of the account (see ``accounts.set_password`` and ``accounts.deactivate``).
- Users revoke their own devices individually (``revoke``); ordinary sign-out
  does not touch devices.
- Trust affects only the account-wide sign-in delay. It never authenticates:
  sessions are a separate table and separate cookie.

Events never contain a token or its hash.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Final

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.core.security import hash_token, new_token
from app.core.security_log import security_event
from app.models.trusted_device import TrustedDevice
from app.models.user import User

MAX_LIFETIME: Final = timedelta(days=30)
RETENTION: Final = timedelta(days=7)
USER_AGENT_MAX_LENGTH: Final = 256


def issue(
    db: Session,
    user: User,
    *,
    now: datetime,
    lifetime: timedelta,
    user_agent: str | None,
) -> str:
    """Create a trusted device for ``user``; returns the token (for the cookie only)."""
    if not timedelta(0) < lifetime <= MAX_LIFETIME:
        raise ValueError("a trusted device lasts between one second and 30 days")
    token = new_token()
    device = TrustedDevice(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=hash_token(token),
        created_at=now,
        expires_at=now + lifetime,
        last_used_at=now,
        user_agent=(user_agent or "")[:USER_AGENT_MAX_LENGTH] or None,
    )
    db.add(device)
    db.flush()
    security_event(
        "auth.device_trusted",
        "Browser trusted for sign-in",
        user_id=str(user.id),
        device_id=str(device.id),
    )
    return token


def find_valid(db: Session, token: str | None, user: User, now: datetime) -> TrustedDevice | None:
    """The device for ``token`` if it is valid for ``user`` right now, otherwise None."""
    if not token or not user.is_active:
        return None
    device = db.scalars(
        select(TrustedDevice).where(TrustedDevice.token_hash == hash_token(token))
    ).one_or_none()
    if device is None:
        return None
    if device.user_id != user.id:
        security_event(
            "auth.device_rejected",
            "Trusted device refused: it belongs to another account",
            level=logging.WARNING,
            user_id=str(user.id),
        )
        return None
    if device.revoked_at is not None or now >= device.expires_at:
        return None
    return device


def mark_used(device: TrustedDevice, now: datetime) -> None:
    device.last_used_at = now


def list_for_user(db: Session, user_id: uuid.UUID, now: datetime) -> list[TrustedDevice]:
    """The user's devices that are still valid, newest first."""
    return list(
        db.scalars(
            select(TrustedDevice)
            .where(
                TrustedDevice.user_id == user_id,
                TrustedDevice.revoked_at.is_(None),
                TrustedDevice.expires_at > now,
            )
            .order_by(TrustedDevice.created_at.desc())
        )
    )


def revoke(
    db: Session, user_id: uuid.UUID, device_id: uuid.UUID, reason: str, now: datetime
) -> bool:
    """Revoke one of the user's devices. False if it is not theirs or already ended."""
    result = db.execute(
        update(TrustedDevice)
        .where(
            TrustedDevice.id == device_id,
            TrustedDevice.user_id == user_id,
            TrustedDevice.revoked_at.is_(None),
        )
        .values(revoked_at=now, revoked_reason=reason)
    )
    revoked = bool(result.rowcount)  # type: ignore[attr-defined]
    if revoked:
        security_event(
            "auth.device_revoked",
            "Trusted device revoked",
            user_id=str(user_id),
            device_id=str(device_id),
            reason=reason,
        )
    return revoked


def revoke_all(db: Session, user_id: uuid.UUID, reason: str, now: datetime) -> int:
    """Revoke every device of the account. Returns the number revoked."""
    result = db.execute(
        update(TrustedDevice)
        .where(TrustedDevice.user_id == user_id, TrustedDevice.revoked_at.is_(None))
        .values(revoked_at=now, revoked_reason=reason)
    )
    count = int(result.rowcount)  # type: ignore[attr-defined]
    if count:
        security_event(
            "auth.devices_revoked",
            "Trusted devices revoked",
            user_id=str(user_id),
            reason=reason,
            revoked_count=count,
        )
    return count


def purge_ended(db: Session, now: datetime) -> int:
    """Delete devices that expired or were revoked more than the retention period ago."""
    cutoff = now - RETENTION
    result = db.execute(
        delete(TrustedDevice).where(
            or_(TrustedDevice.expires_at < cutoff, TrustedDevice.revoked_at < cutoff)
        )
    )
    return int(result.rowcount)  # type: ignore[attr-defined]
