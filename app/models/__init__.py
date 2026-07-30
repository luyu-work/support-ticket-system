"""Модели SQLAlchemy тикет-системы."""

from app.models.base import DatabaseModelBase
from app.models.enums import TicketActivityEventType, TicketProblemReason, TicketStatus, UserRole
from app.models.support_ticket import SupportTicket
from app.models.ticket_activity import TicketActivity
from app.models.ticket_attachment import MAX_ATTACHMENTS_PER_TICKET, TicketAttachment
from app.models.ticket_comment import TicketComment
from app.models.user_account import UserAccount

__all__ = [
    "MAX_ATTACHMENTS_PER_TICKET",
    "DatabaseModelBase",
    "SupportTicket",
    "TicketActivity",
    "TicketActivityEventType",
    "TicketAttachment",
    "TicketComment",
    "TicketProblemReason",
    "TicketStatus",
    "UserAccount",
    "UserRole",
]
