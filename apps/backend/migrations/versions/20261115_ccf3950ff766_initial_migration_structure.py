"""initial migration structure

Baseline revision. It creates no tables: business models are added by later
roadmap phases, each with its own migration that revises this one. Applying
it records the baseline in the ``alembic_version`` table.

Revision ID: ccf3950ff766
Revises:
Create Date: 2026-11-15 14:32:04.338336+00:00
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ccf3950ff766"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
