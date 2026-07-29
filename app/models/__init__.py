"""SQLAlchemy models for the ticket system."""

from app.models.base import DatabaseModelBase
from app.models.enums import TicketActivityEventType, TicketProblemReason, TicketStatus, UserRole
from app.models.support_ticket import SupportTicket
from app.models.ticket_activity import TicketActivity
from app.models.ticket_attachment import MAX_ATTACHMENTS_PER_TICKET, TicketAttachment
from app.models.ticket_comment import TicketComment
from app.models.user_account import UserAccount

__all__ = [
    "DatabaseModelBase",
    "UserAccount",
    "UserRole",
    "SupportTicket",
    "TicketStatus",
    "TicketProblemReason",
    "TicketActivityEventType",
    "TicketComment",
    "TicketActivity",
    "TicketAttachment",
    "MAX_ATTACHMENTS_PER_TICKET",
]
