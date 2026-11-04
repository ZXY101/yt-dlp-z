"""add live chat settings to jobs and presets

Revision ID: 744d978a1094
Revises: c7d2e9a1f304
Create Date: 2026-11-04 13:04:10.411000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "744d978a1094"
down_revision: str | None = "c7d2e9a1f304"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("live_chat", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("chat_status", sa.String(length=20), nullable=True))

    with op.batch_alter_table("presets", schema=None) as batch_op:
        batch_op.add_column(sa.Column("live_chat", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("presets", schema=None) as batch_op:
        batch_op.drop_column("live_chat")

    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_column("chat_status")
        batch_op.drop_column("live_chat")
