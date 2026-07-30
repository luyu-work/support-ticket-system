"""Зависимости FastAPI: сессия БД и текущий пользователь из JWT."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_database_session
from app.core.roles import role_value
from app.core.security import decode_access_token
from app.models import UserAccount, UserRole
from app.services.user_account_service import get_user_account_by_id

bearer_access_token_scheme = HTTPBearer(auto_error=False)

DatabaseSessionDep = Annotated[Session, Depends(get_database_session)]

def get_current_user_account(
    database_session: DatabaseSessionDep,
    bearer_credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_access_token_scheme),
    ],
) -> UserAccount:
    """Читает Bearer JWT и достаёт пользователя из БД."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if bearer_credentials is None:
        raise unauthorized

    try:
        token_payload = decode_access_token(bearer_credentials.credentials)
        user_account_id = int(token_payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as error:
        raise unauthorized from error

    user_account = get_user_account_by_id(database_session, user_account_id)
    if user_account is None or not user_account.is_active:
        raise unauthorized

    return user_account

CurrentUserAccountDep = Annotated[UserAccount, Depends(get_current_user_account)]

def require_admin_role(current_user_account: CurrentUserAccountDep) -> UserAccount:
    if role_value(current_user_account) != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user_account

def require_agent_role(current_user_account: CurrentUserAccountDep) -> UserAccount:
    if role_value(current_user_account) != UserRole.AGENT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent role required",
        )
    return current_user_account

def require_agent_or_admin_role(current_user_account: CurrentUserAccountDep) -> UserAccount:
    if role_value(current_user_account) not in {
        UserRole.AGENT.value,
        UserRole.ADMIN.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent or admin role required",
        )
    return current_user_account

def require_client_role(current_user_account: CurrentUserAccountDep) -> UserAccount:
    if role_value(current_user_account) != UserRole.CLIENT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role required",
        )
    return current_user_account

ClientAccountDep = Annotated[UserAccount, Depends(require_client_role)]
AdminAccountDep = Annotated[UserAccount, Depends(require_admin_role)]
AgentAccountDep = Annotated[UserAccount, Depends(require_agent_role)]
StaffAccountDep = Annotated[UserAccount, Depends(require_agent_or_admin_role)]
