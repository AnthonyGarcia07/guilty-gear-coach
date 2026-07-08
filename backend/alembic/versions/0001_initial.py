"""initial users and matches schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("player_character", sa.String(length=80), nullable=False),
        sa.Column("opponent_character", sa.String(length=80), nullable=False),
        sa.Column("result", sa.String(length=8), nullable=False),
        sa.Column("played_on", sa.Date(), nullable=False),
        sa.Column("rank_floor", sa.String(length=80), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("mistake_tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("strength_tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("reason_for_loss", sa.String(length=160), nullable=True),
        sa.Column("practice_next", sa.Text(), nullable=True),
        sa.Column("replay_filename", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_matches_id"), "matches", ["id"], unique=False)
    op.create_index(op.f("ix_matches_opponent_character"), "matches", ["opponent_character"], unique=False)
    op.create_index(op.f("ix_matches_owner_id"), "matches", ["owner_id"], unique=False)
    op.create_index(op.f("ix_matches_played_on"), "matches", ["played_on"], unique=False)
    op.create_index(op.f("ix_matches_player_character"), "matches", ["player_character"], unique=False)
    op.create_index(op.f("ix_matches_result"), "matches", ["result"], unique=False)


def downgrade() -> None:
    op.drop_table("matches")
    op.drop_table("users")
