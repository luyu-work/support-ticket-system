"""DB access for support tickets, attachments, comments, and activity."""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.models import (
    SupportTicket,
    TicketActivity,
    TicketActivityEventType,
    TicketAttachment,
    TicketComment,
    TicketStatus,
)


def get_ticket_by_id(
    database_session: Session,
    support_ticket_id: int,
) -> SupportTicket | None:
    return database_session.scalar(
        select(SupportTicket)
        .options(
            selectinload(SupportTicket.attachments),
            selectinload(SupportTicket.comments).selectinload(TicketComment.comment_author),
            selectinload(SupportTicket.activity_events).selectinload(TicketActivity.actor),
            selectinload(SupportTicket.assigned_agent),
        )
        .where(SupportTicket.support_ticket_id == support_ticket_id)
    )


def count_tickets_for_client(
    database_session: Session,
    client_author_id: int,
) -> int:
    return (
        database_session.scalar(
            select(func.count())
            .select_from(SupportTicket)
            .where(SupportTicket.client_author_id == client_author_id)
        )
        or 0
    )


def list_tickets_for_client(
    database_session: Session,
    client_author_id: int,
) -> list[SupportTicket]:
    return list(
        database_session.scalars(
            select(SupportTicket)
            .options(selectinload(SupportTicket.attachments))
            .where(SupportTicket.client_author_id == client_author_id)
            .order_by(SupportTicket.created_at.desc())
        ).all()
    )


def list_stale_queue_ticket_ids(
    database_session: Session,
    *,
    created_before: datetime,
) -> list[int]:
    return list(
        database_session.scalars(
            select(SupportTicket.support_ticket_id).where(
                SupportTicket.status == TicketStatus.IN_QUEUE,
                SupportTicket.created_at <= created_before,
            )
        ).all()
    )


def mark_tickets_important(
    database_session: Session,
    ticket_ids: list[int],
) -> None:
    if not ticket_ids:
        return
    database_session.execute(
        update(SupportTicket)
        .where(SupportTicket.support_ticket_id.in_(ticket_ids))
        .values(status=TicketStatus.IMPORTANT)
    )


def list_pool_tickets(
    database_session: Session,
    *,
    status_filter: str | None = None,
) -> list[SupportTicket]:
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
    query = (
        select(SupportTicket)
        .options(selectinload(SupportTicket.assigned_agent))
        .where(SupportTicket.status == TicketStatus.CLOSED)
        .order_by(SupportTicket.support_ticket_id.desc())
    )
    return list(database_session.scalars(query).all())


def add_ticket(
    database_session: Session,
    ticket: SupportTicket,
) -> SupportTicket:
    database_session.add(ticket)
    return ticket


def add_attachment(
    database_session: Session,
    attachment: TicketAttachment,
) -> TicketAttachment:
    database_session.add(attachment)
    return attachment


def add_comment(
    database_session: Session,
    comment: TicketComment,
) -> TicketComment:
    database_session.add(comment)
    return comment


def add_activity(
    database_session: Session,
    *,
    support_ticket_id: int,
    event_type: TicketActivityEventType,
    actor_user_id: int | None = None,
    details: str | None = None,
) -> TicketActivity:
    activity = TicketActivity(
        support_ticket_id=support_ticket_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        details=details,
    )
    database_session.add(activity)
    return activity


def get_attachment_for_ticket(
    database_session: Session,
    *,
    support_ticket_id: int,
    ticket_attachment_id: int,
) -> TicketAttachment | None:
    return database_session.scalar(
        select(TicketAttachment).where(
            TicketAttachment.ticket_attachment_id == ticket_attachment_id,
            TicketAttachment.support_ticket_id == support_ticket_id,
        )
    )
