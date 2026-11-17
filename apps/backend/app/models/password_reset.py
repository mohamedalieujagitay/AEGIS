"""Password reset tokens issued by the instance administrator (PRD FR-AUTH-005).

Only the SHA-256 hash of each token is stored. A token is single-use
(``used_at``) and expires after ``AEGIS_PASSWORD_RESET_TOKEN_TTL_MINUTES``.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class PasswordResetToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        CheckConstraint("issue_method IN ('admin', 'cli')", name="issue_method"),
        CheckConstraint("expires_at > created_at", name="expiry_after_creation"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    issued_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, default=None
    )
    issue_method: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None] = mapped_column(default=None)
