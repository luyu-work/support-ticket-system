"""Admin: manage agents."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminAccountDep, DatabaseSessionDep
from app.schemas.admin import (
    AgentAdminResponse,
    AgentCreateRequest,
    AgentListResponse,
    AgentUpdateRequest,
)
from app.services.agent_admin_service import (
    AgentNotFoundError,
    AgentNumberTakenError,
    AgentValidationError,
    agent_to_response,
    create_agent,
    delete_agent,
    get_agent_by_id,
    list_agents,
    update_agent,
)

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _to_agent_response(agent) -> AgentAdminResponse:
    return AgentAdminResponse(**agent_to_response(agent))


@admin_router.get("/agents", response_model=AgentListResponse)
def list_support_agents(
    database_session: DatabaseSessionDep,
    _admin: AdminAccountDep,
) -> AgentListResponse:
    """Active agents for the admin table."""
    agents = list_agents(database_session, include_inactive=False)
    items = [_to_agent_response(agent) for agent in agents]
    return AgentListResponse(items=items, total_count=len(items))


@admin_router.post(
    "/agents",
    response_model=AgentAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_support_agent(
    body: AgentCreateRequest,
    database_session: DatabaseSessionDep,
    admin: AdminAccountDep,
) -> AgentAdminResponse:
    try:
        agent = create_agent(
            database_session,
            full_name=body.full_name,
            agent_number=body.agent_number,
            plain_password=body.password,
            work_days=body.work_days,
            work_time_start=body.work_time_start,
            work_time_end=body.work_time_end,
        )
    except AgentNumberTakenError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Номер агента уже занят",
        ) from error
    except AgentValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.detail,
        ) from error

    logger.info(
        "Admin created agent | admin_id=%s agent_id=%s",
        admin.user_account_id,
        agent.user_account_id,
    )
    return _to_agent_response(agent)


@admin_router.get("/agents/{user_account_id}", response_model=AgentAdminResponse)
def get_support_agent(
    user_account_id: int,
    database_session: DatabaseSessionDep,
    _admin: AdminAccountDep,
) -> AgentAdminResponse:
    agent = get_agent_by_id(database_session, user_account_id)
    if agent is None or not agent.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return _to_agent_response(agent)


@admin_router.patch("/agents/{user_account_id}", response_model=AgentAdminResponse)
def patch_support_agent(
    user_account_id: int,
    body: AgentUpdateRequest,
    database_session: DatabaseSessionDep,
    admin: AdminAccountDep,
) -> AgentAdminResponse:
    try:
        agent = update_agent(
            database_session,
            user_account_id=user_account_id,
            full_name=body.full_name,
            agent_number=body.agent_number,
            plain_password=body.password,
            work_days=body.work_days,
            work_time_start=body.work_time_start,
            work_time_end=body.work_time_end,
        )
    except AgentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        ) from error
    except AgentNumberTakenError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Номер агента уже занят",
        ) from error
    except AgentValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.detail,
        ) from error

    logger.info(
        "Admin updated agent | admin_id=%s agent_id=%s",
        admin.user_account_id,
        agent.user_account_id,
    )
    return _to_agent_response(agent)


@admin_router.delete(
    "/agents/{user_account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_support_agent(
    user_account_id: int,
    database_session: DatabaseSessionDep,
    admin: AdminAccountDep,
) -> None:
    try:
        delete_agent(database_session, user_account_id=user_account_id)
    except AgentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        ) from error
    logger.info(
        "Admin deleted agent | admin_id=%s agent_id=%s",
        admin.user_account_id,
        user_account_id,
    )
