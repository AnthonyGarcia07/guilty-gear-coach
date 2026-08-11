"""create replays table

Revision ID: 0003_create_replays_table
Revises: 0002_add_coaching_match_fields
Create Date: 2026-08-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_create_replays_table"
down_revision: str | None = "0002_add_coaching_match_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "replays",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source_type IN ('replay_file', 'video', 'external_reference')", name="ck_replays_source_type"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_replays_id"), "replays", ["id"], unique=False)
    op.create_index(op.f("ix_replays_match_id"), "replays", ["match_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_replays_match_id"), table_name="replays")
    op.drop_index(op.f("ix_replays_id"), table_name="replays")
    op.drop_table("replays")
