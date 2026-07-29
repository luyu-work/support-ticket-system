"""agent admin_visible_password column

Revision ID: 20260729_0004
Revises: 20260729_0003
Create Date: 2026-07-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0004"
down_revision: Union[str, None] = "20260729_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_accounts",
        sa.Column("admin_visible_password", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_accounts", "admin_visible_password")
