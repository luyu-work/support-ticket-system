"""Создание и чтение тикетов."""

import logging
import time
from datetime import UTC, datetime, timedelta

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.settings import ApplicationSettings, get_application_settings
from app.models import (
    SupportTicket,
    TicketActivityEventType,
    TicketAttachment,
    TicketComment,
    TicketProblemReason,
    TicketStatus,
    UserAccount,
)
from app.repositories import support_ticket_repository
from app.schemas.tickets import PROBLEM_REASON_LABELS_RU
from app.services.ticket_photo_storage import (
    InvalidTicketPhotoError,
    TooManyTicketPhotosError,
    save_ticket_photo_to_disk,
    validate_ticket_photos,
)

logger = logging.getLogger(__name__)

IMPORTANT_AFTER_HOURS = 8

class UnknownProblemReasonError(Exception):
    def __init__(self, problem_reason: str) -> None:
        self.problem_reason = problem_reason
        super().__init__(problem_reason)

class TicketNotAvailableForClaimError(Exception):
    """Тикет нельзя взять: нет, закрыт или уже у кого-то."""

class TicketAlreadyAssignedError(Exception):
    """Тикет уже держит другой агент."""

class TicketActionNotAllowedError(Exception):
    """Агент не может закрыть или передать этот тикет."""

def build_ticket_title(problem_reason: str, custom_title: str | None) -> str:
    if custom_title and custom_title.strip():
        return custom_title.strip()[:255]
    label = PROBLEM_REASON_LABELS_RU.get(problem_reason, problem_reason)
    return label[:255]

def _record_ticket_activity(
    database_session: Session,
    *,
    support_ticket_id: int,
    event_type: TicketActivityEventType,
    actor_user_id: int | None = None,
    details: str | None = None,
    log_level: int = logging.INFO,
) -> None:
    """Добавляет одно событие в историю (commit снаружи)."""
    support_ticket_repository.add_activity(
        database_session,
        support_ticket_id=support_ticket_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        details=details,
    )
    logger.log(
        log_level,
        "Ticket activity | ticket_id=%s event=%s actor_id=%s",
        support_ticket_id,
        event_type.value,
        actor_user_id,
    )

_PROMOTE_COOLDOWN_SECONDS = 30.0
_last_promote_monotonic: float = 0.0

def reset_promote_cooldown_for_tests() -> None:
    """Для pytest: сбрасываем окно кулдауна promote между тестами."""
    global _last_promote_monotonic
    _last_promote_monotonic = 0.0

def create_support_ticket_for_client(
    database_session: Session,
    *,
    client_account: UserAccount,
    problem_reason: str,
    description: str,
    title: str | None = None,
    photo_files: list[UploadFile] | None = None,
    settings: ApplicationSettings | None = None,
) -> SupportTicket:
    """Клиент создаёт тикет в очереди; фото по желанию, максимум 5."""
    application_settings = settings or get_application_settings()
    normalized_reason = problem_reason.strip()
    valid_reasons = {reason.value for reason in TicketProblemReason}
    if normalized_reason not in valid_reasons:
        raise UnknownProblemReasonError(normalized_reason)

    cleaned_description = description.strip()
    if not cleaned_description:
        raise ValueError("description is empty")

    photos = [photo for photo in (photo_files or []) if photo.filename]
    validate_ticket_photos(photos, application_settings)

    new_ticket = SupportTicket(
        title=build_ticket_title(normalized_reason, title),
        problem_reason=normalized_reason,
        description=cleaned_description,
        status=TicketStatus.IN_QUEUE,
        client_author_id=client_account.user_account_id,
        assigned_agent_id=None,
    )
    support_ticket_repository.add_ticket(database_session, new_ticket)
    database_session.flush()

    for photo_file in photos:
        storage_path, original_file_name = save_ticket_photo_to_disk(
            support_ticket_id=new_ticket.support_ticket_id,
            photo_file=photo_file,
            settings=application_settings,
        )
        support_ticket_repository.add_attachment(
            database_session,
            TicketAttachment(
                support_ticket_id=new_ticket.support_ticket_id,
                storage_path=storage_path,
                original_file_name=original_file_name,
            ),
        )

    _record_ticket_activity(
        database_session,
        support_ticket_id=new_ticket.support_ticket_id,
        event_type=TicketActivityEventType.CREATED,
        actor_user_id=client_account.user_account_id,
    )

    database_session.commit()
    database_session.refresh(new_ticket)
    ticket = get_support_ticket_by_id(database_session, new_ticket.support_ticket_id)
    if ticket is None:
        raise RuntimeError("Ticket disappeared after create")
    return ticket

def get_support_ticket_by_id(
    database_session: Session,
    support_ticket_id: int,
) -> SupportTicket | None:
    return support_ticket_repository.get_ticket_by_id(database_session, support_ticket_id)

def list_tickets_for_client(
    database_session: Session,
    *,
    client_account: UserAccount,
) -> tuple[list[SupportTicket], int]:
    """
    Все тикеты клиента (без пагинации).

    В списке хватает тикета и превью фото — комментарии грузим на деталке.
    """
    client_id = client_account.user_account_id
    total_ticket_count = support_ticket_repository.count_tickets_for_client(
        database_session,
        client_id,
    )
    tickets = support_ticket_repository.list_tickets_for_client(database_session, client_id)
    return tickets, total_ticket_count

def promote_stale_queue_tickets_to_important(
    database_session: Session,
    *,
    force: bool = False,
) -> int:
    """
    Тикеты, которые слишком долго висят в очереди, помечаем как «важные».

    Есть короткий кулдаун, чтобы GET /pool под нагрузкой не сканил каждый раз.
    Возвращает, сколько строк обновили.
    """
    global _last_promote_monotonic

    now = time.monotonic()
    if not force and (now - _last_promote_monotonic) < _PROMOTE_COOLDOWN_SECONDS:
        return 0

    threshold = datetime.now(UTC) - timedelta(hours=IMPORTANT_AFTER_HOURS)
    stale_ids = support_ticket_repository.list_stale_queue_ticket_ids(
        database_session,
        created_before=threshold,
    )
    _last_promote_monotonic = now
    if not stale_ids:
        return 0

    support_ticket_repository.mark_tickets_important(database_session, stale_ids)
    details = f"Более {IMPORTANT_AFTER_HOURS} ч. в очереди"
    for ticket_id in stale_ids:
        _record_ticket_activity(
            database_session,
            support_ticket_id=ticket_id,
            event_type=TicketActivityEventType.MARKED_IMPORTANT,
            actor_user_id=None,
            details=details,
            log_level=logging.DEBUG,
        )
    database_session.commit()
    logger.info("Promoted %s stale ticket(s) to important", len(stale_ids))
    return len(stale_ids)

def list_common_ticket_pool(
    database_session: Session,
    *,
    status_filter: str | None = None,
) -> list[SupportTicket]:
    """
    Общий пул для агентов (и админов): все незакрытые тикеты.
    Перед списком обновляем флаги «важно».
    """
    promote_stale_queue_tickets_to_important(database_session)
    return support_ticket_repository.list_pool_tickets(
        database_session,
        status_filter=status_filter,
    )

def list_archived_tickets(database_session: Session) -> list[SupportTicket]:
    """
    Архив для агентов и админов: только закрытые.
    Сначала самые свежие.
    """
    return support_ticket_repository.list_archived_tickets(database_session)

def claim_ticket_from_pool(
    database_session: Session,
    *,
    support_ticket_id: int,
    agent_account: UserAccount,
) -> SupportTicket:
    """
    Свободный агент берёт тикет из пула:
    назначаем агента и статус in_progress.
    """
    promote_stale_queue_tickets_to_important(database_session)

    ticket = get_support_ticket_by_id(database_session, support_ticket_id)
    if ticket is None:
        raise TicketNotAvailableForClaimError

    if ticket.status == TicketStatus.CLOSED:
        raise TicketNotAvailableForClaimError

    if ticket.status == TicketStatus.TRANSFERRED_TO_ENGINEERS:
        raise TicketNotAvailableForClaimError

    if (
        ticket.assigned_agent_id is not None
        and ticket.assigned_agent_id != agent_account.user_account_id
    ):
        raise TicketAlreadyAssignedError

    already_owned = ticket.assigned_agent_id == agent_account.user_account_id
    ticket.assigned_agent_id = agent_account.user_account_id
    ticket.status = TicketStatus.IN_PROGRESS
    if not already_owned:
        _record_ticket_activity(
            database_session,
            support_ticket_id=ticket.support_ticket_id,
            event_type=TicketActivityEventType.CLAIMED,
            actor_user_id=agent_account.user_account_id,
            details=agent_account.full_name,
        )
    database_session.commit()
    database_session.refresh(ticket)
    claimed = get_support_ticket_by_id(database_session, support_ticket_id)
    if claimed is None:
        raise TicketNotAvailableForClaimError
    return claimed

def format_agent_badge(
    user_account_id: int,
    *,
    agent_number: int | None = None,
) -> str:
    """Бейдж агента: сначала № от админа, иначе id аккаунта."""
    number = agent_number if agent_number is not None else user_account_id
    return f"Агент #{int(number):03d}"

def _assert_agent_owns_ticket(ticket: SupportTicket, agent_account: UserAccount) -> None:
    if ticket.assigned_agent_id != agent_account.user_account_id:
        raise TicketActionNotAllowedError

def close_ticket_by_agent(
    database_session: Session,
    *,
    support_ticket_id: int,
    agent_account: UserAccount,
    comment_text: str,
) -> SupportTicket:
    """Закрывает свой тикет и сохраняет комментарий с итогом."""
    cleaned_comment = comment_text.strip()
    if not cleaned_comment:
        raise TicketActionNotAllowedError

    ticket = get_support_ticket_by_id(database_session, support_ticket_id)
    if ticket is None:
        raise TicketNotAvailableForClaimError
    if ticket.status in {TicketStatus.CLOSED, TicketStatus.TRANSFERRED_TO_ENGINEERS}:
        raise TicketActionNotAllowedError
    _assert_agent_owns_ticket(ticket, agent_account)

    support_ticket_repository.add_comment(
        database_session,
        TicketComment(
            comment_text=cleaned_comment,
            support_ticket_id=ticket.support_ticket_id,
            author_user_id=agent_account.user_account_id,
        ),
    )
    ticket.status = TicketStatus.CLOSED
    _record_ticket_activity(
        database_session,
        support_ticket_id=ticket.support_ticket_id,
        event_type=TicketActivityEventType.CLOSED,
        actor_user_id=agent_account.user_account_id,
        details=cleaned_comment,
    )
    database_session.commit()
    database_session.refresh(ticket)
    closed = get_support_ticket_by_id(database_session, support_ticket_id)
    if closed is None:
        raise TicketNotAvailableForClaimError
    return closed

def transfer_ticket_to_engineers_by_agent(
    database_session: Session,
    *,
    support_ticket_id: int,
    agent_account: UserAccount,
) -> SupportTicket:
    ticket = get_support_ticket_by_id(database_session, support_ticket_id)
    if ticket is None:
        raise TicketNotAvailableForClaimError
    if ticket.status in {TicketStatus.CLOSED, TicketStatus.TRANSFERRED_TO_ENGINEERS}:
        raise TicketActionNotAllowedError
    _assert_agent_owns_ticket(ticket, agent_account)
    ticket.status = TicketStatus.TRANSFERRED_TO_ENGINEERS
    _record_ticket_activity(
        database_session,
        support_ticket_id=ticket.support_ticket_id,
        event_type=TicketActivityEventType.TRANSFERRED_TO_ENGINEERS,
        actor_user_id=agent_account.user_account_id,
        details=agent_account.full_name,
    )
    database_session.commit()
    database_session.refresh(ticket)
    transferred = get_support_ticket_by_id(database_session, support_ticket_id)
    if transferred is None:
        raise TicketNotAvailableForClaimError
    return transferred

__all__ = [
    "IMPORTANT_AFTER_HOURS",
    "InvalidTicketPhotoError",
    "TicketActionNotAllowedError",
    "TicketAlreadyAssignedError",
    "TicketNotAvailableForClaimError",
    "TooManyTicketPhotosError",
    "UnknownProblemReasonError",
    "build_ticket_title",
    "claim_ticket_from_pool",
    "close_ticket_by_agent",
    "create_support_ticket_for_client",
    "format_agent_badge",
    "get_support_ticket_by_id",
    "list_archived_tickets",
    "list_common_ticket_pool",
    "list_tickets_for_client",
    "promote_stale_queue_tickets_to_important",
    "transfer_ticket_to_engineers_by_agent",
]
