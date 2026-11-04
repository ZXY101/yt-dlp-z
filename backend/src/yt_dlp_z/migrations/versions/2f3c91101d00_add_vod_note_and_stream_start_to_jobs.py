"""add vod note and stream start to jobs

Revision ID: 2f3c91101d00
Revises: 1cb9b7c733ea
Create Date: 2026-11-04 14:58:52.366909
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2f3c91101d00"
down_revision: str | None = "1cb9b7c733ea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("vod_note", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("stream_started", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_column("stream_started")
        batch_op.drop_column("vod_note")
