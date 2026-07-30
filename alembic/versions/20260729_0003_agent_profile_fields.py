"""Поля профиля агента в user_accounts.

Revision ID: 20260729_0003
Revises: 20260729_0002
Create Date: 2026-07-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0003"
down_revision: Union[str, None] = "20260729_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("user_accounts", sa.Column("agent_number", sa.Integer(), nullable=True))
    op.add_column("user_accounts", sa.Column("work_days", sa.Text(), nullable=True))
    op.add_column("user_accounts", sa.Column("work_time_start", sa.String(length=5), nullable=True))
    op.add_column("user_accounts", sa.Column("work_time_end", sa.String(length=5), nullable=True))
    op.create_index("ix_user_accounts_agent_number", "user_accounts", ["agent_number"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_user_accounts_agent_number", table_name="user_accounts")
    op.drop_column("user_accounts", "work_time_end")
    op.drop_column("user_accounts", "work_time_start")
    op.drop_column("user_accounts", "work_days")
    op.drop_column("user_accounts", "agent_number")
