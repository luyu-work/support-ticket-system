"""create ticket system tables

Revision ID: 20260729_0001
Revises:
Create Date: 2026-07-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_accounts",
        sa.Column("user_account_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_account_id"),
    )
    op.create_index("ix_user_accounts_email", "user_accounts", ["email"], unique=True)
    op.create_index("ix_user_accounts_role", "user_accounts", ["role"], unique=False)

    op.create_table(
        "support_tickets",
        sa.Column("support_ticket_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("problem_reason", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("client_author_id", sa.Integer(), nullable=False),
        sa.Column("assigned_agent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["assigned_agent_id"],
            ["user_accounts.user_account_id"],
        ),
        sa.ForeignKeyConstraint(
            ["client_author_id"],
            ["user_accounts.user_account_id"],
        ),
        sa.PrimaryKeyConstraint("support_ticket_id"),
    )
    op.create_index(
        "ix_support_tickets_problem_reason",
        "support_tickets",
        ["problem_reason"],
        unique=False,
    )
    op.create_index(
        "ix_support_tickets_status",
        "support_tickets",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_support_tickets_created_at",
        "support_tickets",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_support_tickets_client_author_id",
        "support_tickets",
        ["client_author_id"],
        unique=False,
    )
    op.create_index(
        "ix_support_tickets_assigned_agent_id",
        "support_tickets",
        ["assigned_agent_id"],
        unique=False,
    )

    op.create_table(
        "ticket_attachments",
        sa.Column("ticket_attachment_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("support_ticket_id", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("original_file_name", sa.String(length=255), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["support_ticket_id"],
            ["support_tickets.support_ticket_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("ticket_attachment_id"),
    )
    op.create_index(
        "ix_ticket_attachments_support_ticket_id",
        "ticket_attachments",
        ["support_ticket_id"],
        unique=False,
    )

    op.create_table(
        "ticket_comments",
        sa.Column("ticket_comment_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("support_ticket_id", sa.Integer(), nullable=False),
        sa.Column("author_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_user_id"],
            ["user_accounts.user_account_id"],
        ),
        sa.ForeignKeyConstraint(
            ["support_ticket_id"],
            ["support_tickets.support_ticket_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("ticket_comment_id"),
    )
    op.create_index(
        "ix_ticket_comments_support_ticket_id",
        "ticket_comments",
        ["support_ticket_id"],
        unique=False,
    )
    op.create_index(
        "ix_ticket_comments_author_user_id",
        "ticket_comments",
        ["author_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ticket_comments_author_user_id", table_name="ticket_comments")
    op.drop_index("ix_ticket_comments_support_ticket_id", table_name="ticket_comments")
    op.drop_table("ticket_comments")

    op.drop_index("ix_ticket_attachments_support_ticket_id", table_name="ticket_attachments")
    op.drop_table("ticket_attachments")

    op.drop_index("ix_support_tickets_assigned_agent_id", table_name="support_tickets")
    op.drop_index("ix_support_tickets_client_author_id", table_name="support_tickets")
    op.drop_index("ix_support_tickets_created_at", table_name="support_tickets")
    op.drop_index("ix_support_tickets_status", table_name="support_tickets")
    op.drop_index("ix_support_tickets_problem_reason", table_name="support_tickets")
    op.drop_table("support_tickets")

    op.drop_index("ix_user_accounts_role", table_name="user_accounts")
    op.drop_index("ix_user_accounts_email", table_name="user_accounts")
    op.drop_table("user_accounts")
