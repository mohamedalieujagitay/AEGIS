"""trusted devices

Phase 2.1 remediation (DECISIONS.md D-070): browsers trusted for sign-in are
stored as hashes of their device tokens, so they can be listed, revoked
individually and invalidated by a password change or deactivation. The table
is new and empty; no existing data changes.

Revision ID: c4d8e2f6a7b9
Revises: b3c9d1e2f4a5
Create Date: 2026-11-17 14:00:00+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4d8e2f6a7b9"
down_revision: str | Sequence[str] | None = "b3c9d1e2f4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trusted_devices",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=32), nullable=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "expires_at > created_at",
            name=op.f("ck_trusted_devices_expiry_after_creation"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_trusted_devices_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trusted_devices")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_trusted_devices_token_hash")),
    )
    op.create_index(
        op.f("ix_trusted_devices_user_id"), "trusted_devices", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_trusted_devices_user_id"), table_name="trusted_devices")
    op.drop_table("trusted_devices")
