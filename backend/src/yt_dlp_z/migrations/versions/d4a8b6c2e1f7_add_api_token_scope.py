"""add api token scope

Existing tokens keep full access.

Revision ID: d4a8b6c2e1f7
Revises: 2f3c91101d00
Create Date: 2026-11-10 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4a8b6c2e1f7"
down_revision: str | None = "2f3c91101d00"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("api_tokens", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("scope", sa.String(length=10), server_default="full", nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table("api_tokens", schema=None) as batch_op:
        batch_op.drop_column("scope")
