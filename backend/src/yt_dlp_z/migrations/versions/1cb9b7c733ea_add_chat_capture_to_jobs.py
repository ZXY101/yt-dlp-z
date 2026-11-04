"""add chat capture to jobs

Revision ID: 1cb9b7c733ea
Revises: 744d978a1094
Create Date: 2026-11-04 13:58:50.348537
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1cb9b7c733ea"
down_revision: str | None = "744d978a1094"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("chat_capture", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_column("chat_capture")
