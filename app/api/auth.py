"""Регистрация, вход и профиль текущего пользователя."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserAccountDep, DatabaseSessionDep
from app.core.roles import is_agent
from app.core.security import create_access_token
from app.schemas.auth import (
    AccessTokenResponse,
    ClientRegistrationRequest,
    UserAccountResponse,
    UserLoginRequest,
)
from app.services.user_account_service import (
    EmailAlreadyRegisteredError,
    InactiveUserAccountError,
    InvalidCredentialsError,
    authenticate_user_account,
    register_client_account,
    set_user_online_status,
)

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["auth"])

def _build_access_token_response(user_account) -> AccessTokenResponse:
    access_token = create_access_token(
        {
            "sub": str(user_account.user_account_id),
            "role": user_account.role.value,
            "email": user_account.email,
        }
    )
    return AccessTokenResponse(
        access_token=access_token,
        user_account=UserAccountResponse.model_validate(user_account),
    )

@auth_router.post(
    "/register",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_client(
    registration_request: ClientRegistrationRequest,
    database_session: DatabaseSessionDep,
) -> AccessTokenResponse:
    """
    Регистрация клиента: email, имя и пароль пишутся в БД.
    В ответ отдаём JWT — сразу можно открывать форму тикета.
    """
    try:
        new_client = register_client_account(
            database_session,
            email=str(registration_request.email),
            full_name=registration_request.full_name,
            plain_password=registration_request.password,
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        ) from error

    logger.info("Client registered | user_account_id=%s", new_client.user_account_id)
    return _build_access_token_response(new_client)

@auth_router.post("/login", response_model=AccessTokenResponse)
def login_user_account(
    login_request: UserLoginRequest,
    database_session: DatabaseSessionDep,
) -> AccessTokenResponse:
    """Вход: клиент, агент или админ."""
    try:
        user_account = authenticate_user_account(
            database_session,
            email=str(login_request.email),
            plain_password=login_request.password,
        )
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        ) from error
    except InactiveUserAccountError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        ) from error

    if is_agent(user_account):
        user_account = set_user_online_status(
            database_session,
            user_account=user_account,
            is_online=True,
        )

    logger.info(
        "User logged in | user_account_id=%s role=%s",
        user_account.user_account_id,
        user_account.role,
    )
    return _build_access_token_response(user_account)

@auth_router.post("/logout", response_model=UserAccountResponse)
def logout_user_account(
    database_session: DatabaseSessionDep,
    current_user_account: CurrentUserAccountDep,
) -> UserAccountResponse:
    """При выходе сбрасываем «онлайн» у агента."""
    updated = set_user_online_status(
        database_session,
        user_account=current_user_account,
        is_online=False,
    )
    logger.info("User logged out | user_account_id=%s", updated.user_account_id)
    return UserAccountResponse.model_validate(updated)

@auth_router.get("/me", response_model=UserAccountResponse)
def get_my_user_account(
    current_user_account: CurrentUserAccountDep,
) -> UserAccountResponse:
    """Профиль пользователя из текущего JWT."""
    return UserAccountResponse.model_validate(current_user_account)
