"""add video folder to presets and jobs

Off for existing presets and jobs, so their files stay where they are.

Revision ID: ef2148a0acca
Revises: d4a8b6c2e1f7
Create Date: 2026-11-10 17:29:30.384890
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ef2148a0acca"
down_revision: str | None = "d4a8b6c2e1f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("presets", "jobs")


def upgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("video_folder", sa.Boolean(), server_default="0", nullable=False)
            )


def downgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column("video_folder")
