"""Create and read support tickets."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.settings import ApplicationSettings, get_application_settings
from app.models import (
    SupportTicket,
    TicketActivity,
    TicketActivityEventType,
    TicketAttachment,
    TicketComment,
    TicketProblemReason,
    TicketStatus,
    UserAccount,
)
from app.schemas.tickets import PROBLEM_REASON_LABELS_RU
from app.services.ticket_photo_storage import (
    InvalidTicketPhotoError,
    TooManyTicketPhotosError,
    save_ticket_photo_to_disk,
    validate_ticket_photos,
)

logger = logging.getLogger(__name__)

# Ticket not taken for this long → status "important"
IMPORTANT_AFTER_HOURS = 8


class UnknownProblemReasonError(Exception):
    def __init__(self, problem_reason: str) -> None:
        self.problem_reason = problem_reason
        super().__init__(problem_reason)


class TicketNotAvailableForClaimError(Exception):
    """Ticket cannot be claimed (missing, closed, or already taken)."""


class TicketAlreadyAssignedError(Exception):
    """Another agent already holds this ticket."""


class TicketActionNotAllowedError(Exception):
    """Agent cannot close/transfer this ticket."""


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
) -> None:
    """Append one lifecycle event (not committed by itself)."""
    database_session.add(
        TicketActivity(
            support_ticket_id=support_ticket_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            details=details,
        )
    )
    logger.info(
        "Ticket activity | ticket_id=%s event=%s actor_id=%s",
        support_ticket_id,
        event_type.value,
        actor_user_id,
    )


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
    """Client creates a ticket in queue; optional photos (max 5)."""
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
    database_session.add(new_ticket)
    database_session.flush()  # get support_ticket_id before saving files

    for photo_file in photos:
        storage_path, original_file_name = save_ticket_photo_to_disk(
            support_ticket_id=new_ticket.support_ticket_id,
            photo_file=photo_file,
            settings=application_settings,
        )
        database_session.add(
            TicketAttachment(
                support_ticket_id=new_ticket.support_ticket_id,
                storage_path=storage_path,
                original_file_name=original_file_name,
            )
        )

    _record_ticket_activity(
        database_session,
        support_ticket_id=new_ticket.support_ticket_id,
        event_type=TicketActivityEventType.CREATED,
        actor_user_id=client_account.user_account_id,
    )

    database_session.commit()
    database_session.refresh(new_ticket)
    return get_support_ticket_by_id(database_session, new_ticket.support_ticket_id)


def get_support_ticket_by_id(
    database_session: Session,
    support_ticket_id: int,
) -> SupportTicket | None:
    return database_session.scalar(
        select(SupportTicket)
        .options(
            selectinload(SupportTicket.attachments),
            selectinload(SupportTicket.comments).selectinload(TicketComment.comment_author),
            selectinload(SupportTicket.activity_events).selectinload(TicketActivity.actor),
        )
        .where(SupportTicket.support_ticket_id == support_ticket_id)
    )


def list_tickets_for_client(
    database_session: Session,
    *,
    client_account: UserAccount,
) -> tuple[list[SupportTicket], int]:
    """All tickets of the client (no pagination)."""
    base_filter = SupportTicket.client_author_id == client_account.user_account_id
    total_ticket_count = database_session.scalar(
        select(func.count()).select_from(SupportTicket).where(base_filter)
    ) or 0

    tickets = list(
        database_session.scalars(
            select(SupportTicket)
            .options(
                selectinload(SupportTicket.attachments),
                selectinload(SupportTicket.comments).selectinload(TicketComment.comment_author),
            )
            .where(base_filter)
            .order_by(SupportTicket.created_at.desc())
        ).all()
    )
    return tickets, total_ticket_count


def promote_stale_queue_tickets_to_important(database_session: Session) -> int:
    """
    Tickets still in queue longer than IMPORTANT_AFTER_HOURS become "important".
    Returns how many rows were updated.
    """
    threshold = datetime.now(UTC) - timedelta(hours=IMPORTANT_AFTER_HOURS)
    stale_tickets = list(
        database_session.scalars(
            select(SupportTicket).where(
                SupportTicket.status == TicketStatus.IN_QUEUE,
                SupportTicket.created_at <= threshold,
            )
        ).all()
    )
    for ticket in stale_tickets:
        ticket.status = TicketStatus.IMPORTANT
        _record_ticket_activity(
            database_session,
            support_ticket_id=ticket.support_ticket_id,
            event_type=TicketActivityEventType.MARKED_IMPORTANT,
            actor_user_id=None,
            details=f"Более {IMPORTANT_AFTER_HOURS} ч. в очереди",
        )
    if stale_tickets:
        database_session.commit()
    return len(stale_tickets)


def list_common_ticket_pool(
    database_session: Session,
    *,
    status_filter: str | None = None,
) -> list[SupportTicket]:
    """
    Common pool for agents (and admins): all non-closed tickets.
    Refresh "important" flags before listing.
    """
    promote_stale_queue_tickets_to_important(database_session)

    query = (
        select(SupportTicket)
        .options(selectinload(SupportTicket.assigned_agent))
        .where(SupportTicket.status != TicketStatus.CLOSED)
        .order_by(SupportTicket.support_ticket_id.asc())
    )
    if status_filter:
        query = query.where(SupportTicket.status == status_filter)

    return list(database_session.scalars(query).all())


def list_archived_tickets(database_session: Session) -> list[SupportTicket]:
    """
    Archive for agents and admins: closed tickets only.
    Newest closed tickets first.
    """
    query = (
        select(SupportTicket)
        .options(selectinload(SupportTicket.assigned_agent))
        .where(SupportTicket.status == TicketStatus.CLOSED)
        .order_by(SupportTicket.support_ticket_id.desc())
    )
    return list(database_session.scalars(query).all())


def claim_ticket_from_pool(
    database_session: Session,
    *,
    support_ticket_id: int,
    agent_account: UserAccount,
) -> SupportTicket:
    """
    Free agent takes a ticket from the common pool:
    assign agent + status in_progress.
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

    # Re-open of already owned ticket does not add a second "claimed" event
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
    return get_support_ticket_by_id(database_session, support_ticket_id)  # type: ignore[return-value]


def format_agent_badge(user_account_id: int) -> str:
    return f"Агент #{user_account_id:03d}"


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
    """Close an owned ticket and store the agent's outcome comment."""
    cleaned_comment = comment_text.strip()
    if not cleaned_comment:
        raise TicketActionNotAllowedError

    ticket = get_support_ticket_by_id(database_session, support_ticket_id)
    if ticket is None:
        raise TicketNotAvailableForClaimError
    if ticket.status in {TicketStatus.CLOSED, TicketStatus.TRANSFERRED_TO_ENGINEERS}:
        raise TicketActionNotAllowedError
    _assert_agent_owns_ticket(ticket, agent_account)

    database_session.add(
        TicketComment(
            comment_text=cleaned_comment,
            support_ticket_id=ticket.support_ticket_id,
            author_user_id=agent_account.user_account_id,
        )
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
    return get_support_ticket_by_id(database_session, support_ticket_id)  # type: ignore[return-value]


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
    return get_support_ticket_by_id(database_session, support_ticket_id)  # type: ignore[return-value]


# Re-export for API error handling
__all__ = [
    "UnknownProblemReasonError",
    "TooManyTicketPhotosError",
    "InvalidTicketPhotoError",
    "TicketNotAvailableForClaimError",
    "TicketAlreadyAssignedError",
    "TicketActionNotAllowedError",
    "IMPORTANT_AFTER_HOURS",
    "create_support_ticket_for_client",
    "get_support_ticket_by_id",
    "list_tickets_for_client",
    "list_common_ticket_pool",
    "list_archived_tickets",
    "claim_ticket_from_pool",
    "close_ticket_by_agent",
    "transfer_ticket_to_engineers_by_agent",
    "promote_stale_queue_tickets_to_important",
    "format_agent_badge",
    "build_ticket_title",
]
