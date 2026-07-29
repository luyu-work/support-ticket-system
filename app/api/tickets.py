"""HTTP API for support tickets."""

import logging

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.api.deps import ClientAccountDep, CurrentUserAccountDep, DatabaseSessionDep
from app.schemas.tickets import (
    SupportTicketListResponse,
    SupportTicketResponse,
    TicketProblemReasonOption,
    list_problem_reason_options,
)
from app.services.support_ticket_service import (
    InvalidTicketPhotoError,
    TooManyTicketPhotosError,
    UnknownProblemReasonError,
    create_support_ticket_for_client,
    get_support_ticket_by_id,
    list_tickets_for_client,
)

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
    return SupportTicketResponse.model_validate(new_ticket)


@tickets_router.get("/my", response_model=SupportTicketListResponse)
def list_my_support_tickets(
    database_session: DatabaseSessionDep,
    client_account: ClientAccountDep,
    page_number: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> SupportTicketListResponse:
    """List tickets created by the current client."""
    tickets, total_ticket_count = list_tickets_for_client(
        database_session,
        client_account=client_account,
        page_number=page_number,
        page_size=page_size,
    )
    return SupportTicketListResponse(
        items=[SupportTicketResponse.model_validate(ticket) for ticket in tickets],
        total_ticket_count=total_ticket_count,
        page_number=page_number,
        page_size=page_size,
    )


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

    role_value = (
        current_user_account.role.value
        if hasattr(current_user_account.role, "value")
        else str(current_user_account.role)
    )
    if role_value == "client" and ticket.client_author_id != current_user_account.user_account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ticket")

    return SupportTicketResponse.model_validate(ticket)
