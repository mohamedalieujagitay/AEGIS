"""User accounts (PRD FR-AUTH-001, FR-AUTH-006)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, String, false, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user account. Email address and username are stored normalized (lower case)."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("email = lower(email)", name="email_normalized"),)

    email: Mapped[str] = mapped_column(String(254), unique=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    """Argon2id hash in PHC string format. The password itself is never stored."""

    is_instance_admin: Mapped[bool] = mapped_column(default=False, server_default=false())
    """Instance administrator (FR-AUTH-006). Grants no access to workspace data."""

    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    """Inactive accounts cannot sign in."""

    password_changed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(default=None)
