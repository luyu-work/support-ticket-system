"""Request/response bodies for support tickets."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TicketProblemReason, TicketStatus


class TicketAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_attachment_id: int
    original_file_name: str
    storage_path: str
    uploaded_at: datetime


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


class SupportTicketListResponse(BaseModel):
    items: list[SupportTicketResponse]
    total_ticket_count: int
    page_number: int
    page_size: int


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


def list_problem_reason_options() -> list[TicketProblemReasonOption]:
    return [
        TicketProblemReasonOption(value=reason.value, label_ru=PROBLEM_REASON_LABELS_RU[reason.value])
        for reason in TicketProblemReason
    ]
