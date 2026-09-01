"""add replay video metadata fields

Revision ID: 0006_replay_video_metadata
Revises: 0005_add_replay_storage_fields
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_replay_video_metadata"
down_revision: str | None = "0005_add_replay_storage_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("replays", sa.Column("processing_status", sa.String(length=32), server_default="not_processed", nullable=False))
    op.add_column("replays", sa.Column("processing_error", sa.String(length=255), nullable=True))
    op.add_column("replays", sa.Column("metadata_inspected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("replays", sa.Column("video_duration_seconds", sa.Float(), nullable=True))
    op.add_column("replays", sa.Column("video_width", sa.Integer(), nullable=True))
    op.add_column("replays", sa.Column("video_height", sa.Integer(), nullable=True))
    op.add_column("replays", sa.Column("video_fps", sa.Float(), nullable=True))
    op.add_column("replays", sa.Column("video_codec", sa.String(length=80), nullable=True))
    op.create_check_constraint(
        "ck_replays_processing_status",
        "replays",
        "processing_status IN ('not_processed', 'processing', 'processed', 'failed')",
    )
    op.create_check_constraint(
        "ck_replays_video_duration_seconds_non_negative",
        "replays",
        "video_duration_seconds IS NULL OR video_duration_seconds >= 0",
    )
    op.create_check_constraint(
        "ck_replays_video_width_positive",
        "replays",
        "video_width IS NULL OR video_width > 0",
    )
    op.create_check_constraint(
        "ck_replays_video_height_positive",
        "replays",
        "video_height IS NULL OR video_height > 0",
    )
    op.create_check_constraint(
        "ck_replays_video_fps_positive",
        "replays",
        "video_fps IS NULL OR video_fps > 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_replays_video_fps_positive", "replays", type_="check")
    op.drop_constraint("ck_replays_video_height_positive", "replays", type_="check")
    op.drop_constraint("ck_replays_video_width_positive", "replays", type_="check")
    op.drop_constraint("ck_replays_video_duration_seconds_non_negative", "replays", type_="check")
    op.drop_constraint("ck_replays_processing_status", "replays", type_="check")
    op.drop_column("replays", "video_codec")
    op.drop_column("replays", "video_fps")
    op.drop_column("replays", "video_height")
    op.drop_column("replays", "video_width")
    op.drop_column("replays", "video_duration_seconds")
    op.drop_column("replays", "metadata_inspected_at")
    op.drop_column("replays", "processing_error")
    op.drop_column("replays", "processing_status")
