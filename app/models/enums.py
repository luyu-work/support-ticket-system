"""Перечисления: роли и жизненный цикл тикета."""

from enum import Enum

class UserRole(str, Enum):
    """Кто работает в системе: клиент, агент или админ."""

    CLIENT = "client"
    AGENT = "agent"
    ADMIN = "admin"

class TicketStatus(str, Enum):
    """Статусы тикета по ходу жизни (см. input.md)."""

    IN_QUEUE = "in_queue"
    IMPORTANT = "important"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    TRANSFERRED_TO_ENGINEERS = "transferred_to_engineers"

class TicketProblemReason(str, Enum):
    """
    Причины для селекта у клиента.
    Потом можно добавить новые — в БД это просто строка.
    """

    LOGIN_ISSUE = "login_issue"
    PAYMENT_ISSUE = "payment_issue"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"

class TicketActivityEventType(str, Enum):
    """Типы событий в истории тикета."""

    CREATED = "created"
    CLAIMED = "claimed"
    MARKED_IMPORTANT = "marked_important"
    CLOSED = "closed"
    TRANSFERRED_TO_ENGINEERS = "transferred_to_engineers"
