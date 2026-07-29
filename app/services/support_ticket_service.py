"""Create and read support tickets."""

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.settings import ApplicationSettings, get_application_settings
from app.models import SupportTicket, TicketAttachment, TicketProblemReason, TicketStatus, UserAccount
from app.schemas.tickets import PROBLEM_REASON_LABELS_RU
from app.services.ticket_photo_storage import (
    InvalidTicketPhotoError,
    TooManyTicketPhotosError,
    save_ticket_photo_to_disk,
    validate_ticket_photos,
)


class UnknownProblemReasonError(Exception):
    def __init__(self, problem_reason: str) -> None:
        self.problem_reason = problem_reason
        super().__init__(problem_reason)


def build_ticket_title(problem_reason: str, custom_title: str | None) -> str:
    if custom_title and custom_title.strip():
        return custom_title.strip()[:255]
    label = PROBLEM_REASON_LABELS_RU.get(problem_reason, problem_reason)
    return label[:255]


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

    database_session.commit()
    database_session.refresh(new_ticket)
    return get_support_ticket_by_id(database_session, new_ticket.support_ticket_id)


def get_support_ticket_by_id(
    database_session: Session,
    support_ticket_id: int,
) -> SupportTicket | None:
    return database_session.scalar(
        select(SupportTicket)
        .options(selectinload(SupportTicket.attachments))
        .where(SupportTicket.support_ticket_id == support_ticket_id)
    )


def list_tickets_for_client(
    database_session: Session,
    *,
    client_account: UserAccount,
    page_number: int = 1,
    page_size: int = 20,
) -> tuple[list[SupportTicket], int]:
    safe_page_number = max(page_number, 1)
    safe_page_size = min(max(page_size, 1), 100)
    offset = (safe_page_number - 1) * safe_page_size

    base_filter = SupportTicket.client_author_id == client_account.user_account_id
    total_ticket_count = database_session.scalar(
        select(func.count()).select_from(SupportTicket).where(base_filter)
    ) or 0

    tickets = list(
        database_session.scalars(
            select(SupportTicket)
            .options(selectinload(SupportTicket.attachments))
            .where(base_filter)
            .order_by(SupportTicket.created_at.desc())
            .offset(offset)
            .limit(safe_page_size)
        ).all()
    )
    return tickets, total_ticket_count


# Re-export for API error handling
__all__ = [
    "UnknownProblemReasonError",
    "TooManyTicketPhotosError",
    "InvalidTicketPhotoError",
    "create_support_ticket_for_client",
    "get_support_ticket_by_id",
    "list_tickets_for_client",
    "build_ticket_title",
]
