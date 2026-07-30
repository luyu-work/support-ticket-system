"""Data access layer: SQLAlchemy queries live here, not in services."""

from app.repositories.support_ticket_repository import (
    add_activity,
    add_attachment,
    add_comment,
    add_ticket,
    count_tickets_for_client,
    get_attachment_for_ticket,
    get_ticket_by_id,
    list_archived_tickets,
    list_pool_tickets,
    list_stale_queue_ticket_ids,
    list_tickets_for_client,
    mark_tickets_important,
)
from app.repositories.user_account_repository import (
    add_user_account,
    get_agent_by_id,
    get_user_account_by_agent_number,
    get_user_account_by_email,
    get_user_account_by_id,
    list_agents,
)

__all__ = [
    "add_activity",
    "add_attachment",
    "add_comment",
    "add_ticket",
    "add_user_account",
    "count_tickets_for_client",
    "get_agent_by_id",
    "get_attachment_for_ticket",
    "get_ticket_by_id",
    "get_user_account_by_agent_number",
    "get_user_account_by_email",
    "get_user_account_by_id",
    "list_agents",
    "list_archived_tickets",
    "list_pool_tickets",
    "list_stale_queue_ticket_ids",
    "list_tickets_for_client",
    "mark_tickets_important",
]
