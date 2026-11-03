"""split media layout into folders, file name and media files

Revision ID: b3f1c2d4e5a6
Revises: 44f47d865148
Create Date: 2026-11-04 00:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3f1c2d4e5a6"
down_revision: str | None = "44f47d865148"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("jobs", "presets")


def upgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column("folders", sa.String(length=20), nullable=True))
            batch_op.add_column(sa.Column("file_name", sa.String(length=20), nullable=True))
            batch_op.add_column(
                sa.Column("media_files", sa.Boolean(), server_default="0", nullable=False)
            )
        # "season" and "flat" were TV-episode names with media files, with or without
        # season folders.
        op.execute(
            f"UPDATE {table} SET file_name = 'episode', media_files = 1, "  # noqa: S608
            "folders = CASE media_layout WHEN 'season' THEN 'season' ELSE 'channel' END "
            "WHERE media_layout IS NOT NULL"
        )
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column("media_layout")


def downgrade() -> None:
    for table in TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column("media_layout", sa.String(length=20), nullable=True))
        op.execute(
            f"UPDATE {table} SET media_layout = "  # noqa: S608
            "CASE folders WHEN 'season' THEN 'season' ELSE 'flat' END "
            "WHERE file_name = 'episode' AND media_files = 1"
        )
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column("media_files")
            batch_op.drop_column("file_name")
            batch_op.drop_column("folders")
