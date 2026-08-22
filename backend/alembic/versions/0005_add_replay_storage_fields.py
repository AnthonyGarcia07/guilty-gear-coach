"""add replay storage fields

Revision ID: 0005_add_replay_storage_fields
Revises: 0004_backfill_legacy_replays
Create Date: 2026-08-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_replay_storage_fields"
down_revision: str | None = "0004_backfill_legacy_replays"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("replays", sa.Column("storage_key", sa.String(length=1024), nullable=True))
    op.add_column("replays", sa.Column("upload_status", sa.String(length=32), server_default="metadata_only", nullable=False))
    op.add_column("replays", sa.Column("content_type", sa.String(length=255), nullable=True))
    op.add_column("replays", sa.Column("size_bytes", sa.BigInteger(), nullable=True))
    op.add_column("replays", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_replays_upload_status",
        "replays",
        "upload_status IN ('metadata_only', 'pending_upload', 'uploaded')",
    )
    op.create_check_constraint(
        "ck_replays_size_bytes_non_negative",
        "replays",
        "size_bytes IS NULL OR size_bytes >= 0",
    )
    op.create_index(op.f("ix_replays_storage_key"), "replays", ["storage_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_replays_storage_key"), table_name="replays")
    op.drop_constraint("ck_replays_size_bytes_non_negative", "replays", type_="check")
    op.drop_constraint("ck_replays_upload_status", "replays", type_="check")
    op.drop_column("replays", "uploaded_at")
    op.drop_column("replays", "size_bytes")
    op.drop_column("replays", "content_type")
    op.drop_column("replays", "upload_status")
    op.drop_column("replays", "storage_key")
