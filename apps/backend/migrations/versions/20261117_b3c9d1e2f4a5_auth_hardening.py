"""auth hardening

Phase 2.1 remediation (DECISIONS.md D-071, D-072):

- A CHECK constraint keeps stored email addresses in their normalized form
  (lower case, IDNA domain). The application already writes only normalized
  addresses, so the constraint is added without changing any data; if a
  non-normalized row ever existed, this migration fails and changes nothing.
- An index on password_reset_tokens.issued_by_user_id, used by the foreign key
  (ON DELETE SET NULL) and by lookups of who issued a token.

Revision ID: b3c9d1e2f4a5
Revises: a74571505785
Create Date: 2026-11-17 12:00:00+00:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c9d1e2f4a5"
down_revision: str | Sequence[str] | None = "a74571505785"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(op.f("ck_users_email_normalized"), "users", "email = lower(email)")
    op.create_index(
        op.f("ix_password_reset_tokens_issued_by_user_id"),
        "password_reset_tokens",
        ["issued_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_password_reset_tokens_issued_by_user_id"), table_name="password_reset_tokens"
    )
    op.drop_constraint(op.f("ck_users_email_normalized"), "users", type_="check")
