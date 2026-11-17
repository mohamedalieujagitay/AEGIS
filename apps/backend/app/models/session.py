"""Server-side sessions (PRD FR-AUTH-003, DECISIONS.md D-064).

The browser holds a random token in an HttpOnly cookie; this table holds
only its SHA-256 hash. A session is valid while it is not revoked, its
absolute expiry has not passed and it has been used within the idle timeout.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class UserSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_sessions"
    __table_args__ = (CheckConstraint("expires_at > created_at", name="expiry_after_creation"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime]
    last_seen_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    """Absolute expiry, set at sign-in."""

    revoked_at: Mapped[datetime | None] = mapped_column(default=None)
    revoked_reason: Mapped[str | None] = mapped_column(String(32), default=None)
    ip_address: Mapped[str | None] = mapped_column(INET, default=None)
    """Client address at sign-in, for the session list of roadmap task 2.2. Never logged."""

    user_agent: Mapped[str | None] = mapped_column(String(256), default=None)
