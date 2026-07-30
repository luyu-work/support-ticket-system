"""Таблица истории событий по тикету.

Revision ID: 20260729_0002
Revises: 20260729_0001
Create Date: 2026-07-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0002"
down_revision: Union[str, None] = "20260729_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "ticket_activities",
        sa.Column("ticket_activity_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("support_ticket_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["user_accounts.user_account_id"],
        ),
        sa.ForeignKeyConstraint(
            ["support_ticket_id"],
            ["support_tickets.support_ticket_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("ticket_activity_id"),
    )
    op.create_index(
        "ix_ticket_activities_event_type",
        "ticket_activities",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_ticket_activities_support_ticket_id",
        "ticket_activities",
        ["support_ticket_id"],
        unique=False,
    )
    op.create_index(
        "ix_ticket_activities_actor_user_id",
        "ticket_activities",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_ticket_activities_created_at",
        "ticket_activities",
        ["created_at"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index("ix_ticket_activities_created_at", table_name="ticket_activities")
    op.drop_index("ix_ticket_activities_actor_user_id", table_name="ticket_activities")
    op.drop_index("ix_ticket_activities_support_ticket_id", table_name="ticket_activities")
    op.drop_index("ix_ticket_activities_event_type", table_name="ticket_activities")
    op.drop_table("ticket_activities")
