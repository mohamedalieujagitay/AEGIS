"""Trusted devices for sign-in (DECISIONS.md D-070).

A trusted device is a browser that signed in with the password recently. Its
cookie carries a random token; this table holds only the SHA-256 hash of that
token, so a database read does not reveal a usable device token. A device
exempts its browser from the account-wide sign-in delay and from nothing else;
it never authenticates a user (sessions are a separate table).
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class TrustedDevice(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "trusted_devices"
    __table_args__ = (CheckConstraint("expires_at > created_at", name="expiry_after_creation"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    """SHA-256 of the device token. The token itself is never stored or logged."""

    created_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    """Fixed at creation: at most 30 days later. Trust is never extended by use."""

    last_used_at: Mapped[datetime | None] = mapped_column(default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(default=None)
    revoked_reason: Mapped[str | None] = mapped_column(String(32), default=None)
    user_agent: Mapped[str | None] = mapped_column(String(256), default=None)
