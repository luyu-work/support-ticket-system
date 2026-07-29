"""HTTP API for support tickets."""

import logging
import mimetypes
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import (
    AgentAccountDep,
    ClientAccountDep,
    CurrentUserAccountDep,
    DatabaseSessionDep,
    StaffAccountDep,
)
from app.core.roles import is_client, is_staff
from app.models import TicketAttachment
from app.schemas.tickets import (
    PROBLEM_REASON_LABELS_RU,
    CloseTicketRequest,
    PoolTicketAssignee,
    PoolTicketItem,
    SupportTicketListResponse,
    SupportTicketResponse,
    TicketPoolListResponse,
    TicketProblemReasonOption,
    list_problem_reason_options,
    to_support_ticket_response,
)
from app.services.support_ticket_service import (
    InvalidTicketPhotoError,
    TicketActionNotAllowedError,
    TicketAlreadyAssignedError,
    TicketNotAvailableForClaimError,
    TooManyTicketPhotosError,
    UnknownProblemReasonError,
    claim_ticket_from_pool,
    close_ticket_by_agent,
    create_support_ticket_for_client,
    format_agent_badge,
    get_support_ticket_by_id,
    list_archived_tickets,
    list_common_ticket_pool,
    list_tickets_for_client,
    transfer_ticket_to_engineers_by_agent,
)
from app.services.ticket_photo_storage import get_ticket_uploads_root

logger = logging.getLogger(__name__)

tickets_router = APIRouter(prefix="/tickets", tags=["tickets"])


@tickets_router.get("/problem-reasons", response_model=list[TicketProblemReasonOption])
def get_problem_reason_options() -> list[TicketProblemReasonOption]:
    """Select options for the ticket form (list of reasons)."""
    return list_problem_reason_options()


@tickets_router.post(
    "",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_support_ticket(
    database_session: DatabaseSessionDep,
    client_account: ClientAccountDep,
    problem_reason: str = Form(...),
    description: str = Form(...),
    title: str | None = Form(None),
    photos: list[UploadFile] | None = File(None),
) -> SupportTicketResponse:
    """
    Client creates a ticket.
    multipart/form-data: problem_reason, description, optional title, optional photos.
    """
    photo_files = photos or []
    try:
        new_ticket = create_support_ticket_for_client(
            database_session,
            client_account=client_account,
            problem_reason=problem_reason,
            description=description,
            title=title,
            photo_files=photo_files,
        )
    except UnknownProblemReasonError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown problem_reason: {error.problem_reason}",
        ) from error
    except TooManyTicketPhotosError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum 5 photos allowed, got {error.photo_count}",
        ) from error
    except InvalidTicketPhotoError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.detail,
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    logger.info(
        "Ticket created | ticket_id=%s client_id=%s",
        new_ticket.support_ticket_id,
        client_account.user_account_id,
    )
    return to_support_ticket_response(new_ticket, include_activity_log=False)


@tickets_router.get("/my", response_model=SupportTicketListResponse)
def list_my_support_tickets(
    database_session: DatabaseSessionDep,
    client_account: ClientAccountDep,
) -> SupportTicketListResponse:
    """List all tickets created by the current client (no pagination)."""
    tickets, total_ticket_count = list_tickets_for_client(
        database_session,
        client_account=client_account,
    )
    return SupportTicketListResponse(
        items=[
            to_support_ticket_response(
                ticket,
                include_activity_log=False,
                include_comments=False,
            )
            for ticket in tickets
        ],
        total_ticket_count=total_ticket_count,
    )


def _tickets_to_pool_items(tickets: list) -> list[PoolTicketItem]:
    items: list[PoolTicketItem] = []
    for ticket in tickets:
        assignee = None
        if ticket.assigned_agent is not None:
            agent = ticket.assigned_agent
            assignee = PoolTicketAssignee(
                user_account_id=agent.user_account_id,
                full_name=agent.full_name,
                agent_badge=format_agent_badge(
                    agent.user_account_id,
                    agent_number=agent.agent_number,
                ),
            )
        items.append(
            PoolTicketItem(
                support_ticket_id=ticket.support_ticket_id,
                status=ticket.status,
                created_at=ticket.created_at,
                problem_reason=ticket.problem_reason,
                problem_reason_label=PROBLEM_REASON_LABELS_RU.get(
                    ticket.problem_reason,
                    ticket.problem_reason,
                ),
                assigned_agent=assignee,
            )
        )
    return items


_POOL_STATUS_FILTERS = frozenset(
    {
        "in_queue",
        "important",
        "in_progress",
        "transferred_to_engineers",
    }
)


@tickets_router.get("/pool", response_model=TicketPoolListResponse)
def list_ticket_pool(
    database_session: DatabaseSessionDep,
    _staff_account: StaffAccountDep,
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Optional filter: in_queue | important | in_progress | transferred_to_engineers",
    ),
) -> TicketPoolListResponse:
    """
    Common ticket pool for agents (and admins).
    Any free agent can claim an unassigned ticket from this list.
    Closed tickets live in /tickets/archive.
    """
    if status_filter is not None and status_filter not in _POOL_STATUS_FILTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid status filter. Allowed: "
                + ", ".join(sorted(_POOL_STATUS_FILTERS))
            ),
        )
    tickets = list_common_ticket_pool(database_session, status_filter=status_filter)
    items = _tickets_to_pool_items(tickets)
    return TicketPoolListResponse(items=items, total_ticket_count=len(items))


@tickets_router.get("/archive", response_model=TicketPoolListResponse)
def list_ticket_archive(
    database_session: DatabaseSessionDep,
    _staff_account: StaffAccountDep,
) -> TicketPoolListResponse:
    """
    Archive of closed tickets for agents and admins (read-only list).
    """
    tickets = list_archived_tickets(database_session)
    items = _tickets_to_pool_items(tickets)
    return TicketPoolListResponse(items=items, total_ticket_count=len(items))


@tickets_router.post(
    "/{support_ticket_id}/claim",
    response_model=SupportTicketResponse,
)
def claim_support_ticket(
    support_ticket_id: int,
    database_session: DatabaseSessionDep,
    agent_account: AgentAccountDep,
) -> SupportTicketResponse:
    """Agent takes a ticket from the common pool into work."""
    try:
        ticket = claim_ticket_from_pool(
            database_session,
            support_ticket_id=support_ticket_id,
            agent_account=agent_account,
        )
    except TicketNotAvailableForClaimError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket is not available in the pool",
        ) from error
    except TicketAlreadyAssignedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ticket already assigned to another agent",
        ) from error

    logger.info(
        "Ticket claimed | ticket_id=%s agent_id=%s",
        support_ticket_id,
        agent_account.user_account_id,
    )
    return to_support_ticket_response(ticket)


@tickets_router.post(
    "/{support_ticket_id}/close",
    response_model=SupportTicketResponse,
)
def close_support_ticket(
    support_ticket_id: int,
    body: CloseTicketRequest,
    database_session: DatabaseSessionDep,
    agent_account: AgentAccountDep,
) -> SupportTicketResponse:
    """Agent closes a ticket they own and leaves an outcome comment."""
    try:
        ticket = close_ticket_by_agent(
            database_session,
            support_ticket_id=support_ticket_id,
            agent_account=agent_account,
            comment_text=body.comment_text,
        )
    except TicketNotAvailableForClaimError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error
    except TicketActionNotAllowedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot close this ticket",
        ) from error
    return to_support_ticket_response(ticket)


@tickets_router.post(
    "/{support_ticket_id}/transfer-to-engineers",
    response_model=SupportTicketResponse,
)
def transfer_support_ticket_to_engineers(
    support_ticket_id: int,
    database_session: DatabaseSessionDep,
    agent_account: AgentAccountDep,
) -> SupportTicketResponse:
    """Agent transfers a ticket they own to engineers."""
    try:
        ticket = transfer_ticket_to_engineers_by_agent(
            database_session,
            support_ticket_id=support_ticket_id,
            agent_account=agent_account,
        )
    except TicketNotAvailableForClaimError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        ) from error
    except TicketActionNotAllowedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot transfer this ticket",
        ) from error
    return to_support_ticket_response(ticket)


def _assert_user_can_view_ticket(current_user_account, ticket) -> None:
    if (
        is_client(current_user_account)
        and ticket.client_author_id != current_user_account.user_account_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ticket")


@tickets_router.get("/{support_ticket_id}", response_model=SupportTicketResponse)
def get_support_ticket_detail(
    support_ticket_id: int,
    database_session: DatabaseSessionDep,
    current_user_account: CurrentUserAccountDep,
) -> SupportTicketResponse:
    """
    Get one ticket.
    Client — only own tickets. Agent/admin — any ticket (for next steps).
    """
    ticket = get_support_ticket_by_id(database_session, support_ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    _assert_user_can_view_ticket(current_user_account, ticket)
    # Activity log is staff-only; clients still receive agent comments
    return to_support_ticket_response(
        ticket,
        include_activity_log=is_staff(current_user_account),
    )


@tickets_router.get(
    "/{support_ticket_id}/attachments/{ticket_attachment_id}/file",
    include_in_schema=False,
)
def download_ticket_attachment_file(
    support_ticket_id: int,
    ticket_attachment_id: int,
    database_session: DatabaseSessionDep,
    current_user_account: CurrentUserAccountDep,
) -> FileResponse:
    """Serve a ticket photo (auth required)."""
    ticket = get_support_ticket_by_id(database_session, support_ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    _assert_user_can_view_ticket(current_user_account, ticket)

    attachment = database_session.scalar(
        select(TicketAttachment).where(
            TicketAttachment.ticket_attachment_id == ticket_attachment_id,
            TicketAttachment.support_ticket_id == support_ticket_id,
        )
    )
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    file_path = Path(attachment.storage_path)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path
    file_path = file_path.resolve()

    # Only serve files under the configured uploads root (path traversal guard)
    uploads_root = get_ticket_uploads_root().resolve()
    try:
        file_path.relative_to(uploads_root)
    except ValueError as error:
        logger.warning(
            "Attachment path outside uploads root | ticket_id=%s path=%s",
            support_ticket_id,
            file_path,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        ) from error

    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing on disk")

    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        path=file_path,
        media_type=media_type or "application/octet-stream",
        filename=attachment.original_file_name,
    )
