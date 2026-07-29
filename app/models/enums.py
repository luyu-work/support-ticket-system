"""Business enums for roles and ticket lifecycle."""

from enum import Enum


class UserRole(str, Enum):
    """Who is using the ticket system."""

    CLIENT = "client"  # обычный пользователь (создаёт тикеты)
    AGENT = "agent"  # агент поддержки
    ADMIN = "admin"  # администратор


class TicketStatus(str, Enum):
    """Lifecycle of a support ticket (see input.md)."""

    IN_QUEUE = "in_queue"  # в очереди / в пуле
    IMPORTANT = "important"  # не обработан дольше 8 часов
    IN_PROGRESS = "in_progress"  # агент взял в работу
    CLOSED = "closed"  # агент закрыл
    TRANSFERRED_TO_ENGINEERS = "transferred_to_engineers"  # передан инженерам


class TicketProblemReason(str, Enum):
    """
    Default reasons for the client select.
    Easy to extend later without changing the Ticket column type (stored as string).
    """

    LOGIN_ISSUE = "login_issue"
    PAYMENT_ISSUE = "payment_issue"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"
