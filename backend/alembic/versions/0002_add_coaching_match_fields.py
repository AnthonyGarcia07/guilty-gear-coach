"""add coaching match fields

Revision ID: 0002_add_coaching_match_fields
Revises: 0001_initial
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_coaching_match_fields"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("rounds_won", sa.Integer(), nullable=True))
    op.add_column("matches", sa.Column("rounds_lost", sa.Integer(), nullable=True))
    op.add_column("matches", sa.Column("first_to", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "first_to")
    op.drop_column("matches", "rounds_lost")
    op.drop_column("matches", "rounds_won")
