"""Request/response bodies for support tickets."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TicketActivityEventType, TicketProblemReason, TicketStatus


class TicketAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_attachment_id: int
    original_file_name: str
    storage_path: str
    uploaded_at: datetime


class TicketCommentResponse(BaseModel):
    ticket_comment_id: int
    comment_text: str
    author_user_id: int
    author_full_name: str | None = None
    created_at: datetime


class TicketActivityEventResponse(BaseModel):
    ticket_activity_id: int
    event_type: str
    event_label_ru: str
    actor_user_id: int | None = None
    actor_full_name: str | None = None
    details: str | None = None
    created_at: datetime


class SupportTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    support_ticket_id: int
    title: str
    problem_reason: str
    description: str
    status: TicketStatus
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    client_author_id: int
    assigned_agent_id: int | None
    attachments: list[TicketAttachmentResponse] = Field(default_factory=list)
    comments: list[TicketCommentResponse] = Field(default_factory=list)
    activity_log: list[TicketActivityEventResponse] = Field(default_factory=list)


class SupportTicketListResponse(BaseModel):
    items: list[SupportTicketResponse]
    total_ticket_count: int


class PoolTicketAssignee(BaseModel):
    user_account_id: int
    full_name: str
    agent_badge: str  # e.g. "Агент #001"


class PoolTicketItem(BaseModel):
    support_ticket_id: int
    status: TicketStatus
    created_at: datetime
    problem_reason: str
    problem_reason_label: str
    assigned_agent: PoolTicketAssignee | None = None


class TicketPoolListResponse(BaseModel):
    items: list[PoolTicketItem]
    total_ticket_count: int


class CloseTicketRequest(BaseModel):
    """Agent must leave a short outcome comment when closing a ticket."""

    comment_text: str = Field(min_length=1, max_length=4000)


class TicketProblemReasonOption(BaseModel):
    value: str
    label_ru: str


PROBLEM_REASON_LABELS_RU: dict[str, str] = {
    TicketProblemReason.BUG_REPORT.value: "Баги",
    TicketProblemReason.PAYMENT_ISSUE.value: "Проблема с оплатой",
    TicketProblemReason.FEATURE_REQUEST.value: "Предложения по улучшению",
    TicketProblemReason.LOGIN_ISSUE.value: "Проблема со входом",
    TicketProblemReason.OTHER.value: "Другое",
}

ACTIVITY_EVENT_LABELS_RU: dict[str, str] = {
    TicketActivityEventType.CREATED.value: "Тикет создан",
    TicketActivityEventType.CLAIMED.value: "Взят в работу",
    TicketActivityEventType.MARKED_IMPORTANT.value: "Отмечен как важное",
    TicketActivityEventType.CLOSED.value: "Тикет закрыт",
    TicketActivityEventType.TRANSFERRED_TO_ENGINEERS.value: "Передан инженерам",
}


_PROBLEM_REASON_OPTIONS_CACHE: list[TicketProblemReasonOption] | None = None


def list_problem_reason_options() -> list[TicketProblemReasonOption]:
    """Static catalog — cache once (metric: problem_reasons latency)."""
    global _PROBLEM_REASON_OPTIONS_CACHE
    if _PROBLEM_REASON_OPTIONS_CACHE is None:
        _PROBLEM_REASON_OPTIONS_CACHE = [
            TicketProblemReasonOption(
                value=reason.value,
                label_ru=PROBLEM_REASON_LABELS_RU[reason.value],
            )
            for reason in TicketProblemReason
        ]
    return _PROBLEM_REASON_OPTIONS_CACHE


def to_support_ticket_response(
    ticket: Any,
    *,
    include_activity_log: bool = True,
    include_comments: bool = True,
) -> SupportTicketResponse:
    """Map ORM ticket (+ comments, activity) to API response with Russian labels.

    Activity log is for agent/admin only — pass include_activity_log=False for clients.
    Comments can be skipped on list endpoints (loaded on detail).
    """
    comments: list[TicketCommentResponse] = []
    if include_comments:
        for comment in sorted(
            getattr(ticket, "comments", None) or [],
            key=lambda item: item.created_at,
        ):
            author = getattr(comment, "comment_author", None)
            comments.append(
                TicketCommentResponse(
                    ticket_comment_id=comment.ticket_comment_id,
                    comment_text=comment.comment_text,
                    author_user_id=comment.author_user_id,
                    author_full_name=author.full_name if author is not None else None,
                    created_at=comment.created_at,
                )
            )

    activity_log: list[TicketActivityEventResponse] = []
    if include_activity_log:
        for event in sorted(
            getattr(ticket, "activity_events", None) or [],
            key=lambda item: item.created_at,
        ):
            event_type_value = (
                event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type)
            )
            actor = getattr(event, "actor", None)
            activity_log.append(
                TicketActivityEventResponse(
                    ticket_activity_id=event.ticket_activity_id,
                    event_type=event_type_value,
                    event_label_ru=ACTIVITY_EVENT_LABELS_RU.get(
                        event_type_value,
                        event_type_value,
                    ),
                    actor_user_id=event.actor_user_id,
                    actor_full_name=actor.full_name if actor is not None else None,
                    details=event.details,
                    created_at=event.created_at,
                )
            )

    return SupportTicketResponse(
        support_ticket_id=ticket.support_ticket_id,
        title=ticket.title,
        problem_reason=ticket.problem_reason,
        description=ticket.description,
        status=ticket.status,
        due_date=ticket.due_date,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        client_author_id=ticket.client_author_id,
        assigned_agent_id=ticket.assigned_agent_id,
        attachments=[
            TicketAttachmentResponse.model_validate(attachment)
            for attachment in (ticket.attachments or [])
        ],
        comments=comments,
        activity_log=activity_log,
    )
