"""backfill legacy replay filename metadata

Revision ID: 0004_backfill_legacy_replays
Revises: 0003_create_replays_table
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_backfill_legacy_replays"
down_revision: str | None = "0003_create_replays_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO replays (match_id, source_type, original_filename, created_at, updated_at)
            SELECT matches.id, 'replay_file', btrim(matches.replay_filename), now(), now()
            FROM matches
            WHERE matches.replay_filename IS NOT NULL
              AND btrim(matches.replay_filename) <> ''
              AND NOT EXISTS (
                  SELECT 1
                  FROM replays
                  WHERE replays.match_id = matches.id
                    AND replays.source_type = 'replay_file'
                    AND btrim(coalesce(replays.original_filename, '')) = btrim(matches.replay_filename)
              )
            """
        )
    )


def downgrade() -> None:
    pass
