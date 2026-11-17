"""Instance-wide settings changed at runtime by the instance administrator (FR-AUTH-006).

A single row (``id = 1``), created by the migration.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, SmallInteger, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class InstanceSettings(Base):
    __tablename__ = "instance_settings"
    __table_args__ = (CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    registration_enabled: Mapped[bool] = mapped_column(default=False, server_default=false())
    """Open self-registration. Disabled by default (FR-AUTH-001)."""

    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
