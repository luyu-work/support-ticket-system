"""Tests for registration, login, JWT, and staff seed."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_plain_password, verify_plain_password
from app.core.settings import get_application_settings
from app.models import UserAccount, UserRole
from app.services.seed_staff_accounts import seed_default_staff_accounts
from app.services.user_account_service import register_client_account


def test_password_hash_and_verify() -> None:
    hashed_password = hash_plain_password("SecretPass123")
    assert hashed_password != "SecretPass123"
    assert verify_plain_password("SecretPass123", hashed_password)
    assert not verify_plain_password("WrongPassword", hashed_password)


def test_access_token_roundtrip() -> None:
    access_token = create_access_token({"sub": "42", "role": "client"})
    assert isinstance(access_token, str)
    assert len(access_token) > 20


def test_seed_creates_admin_and_agent(database_session: Session) -> None:
    settings = get_application_settings()
    seed_default_staff_accounts(database_session, settings)

    admin_account = database_session.scalar(
        select(UserAccount).where(UserAccount.email == settings.seed_admin_email)
    )
    agent_account = database_session.scalar(
        select(UserAccount).where(UserAccount.email == settings.seed_agent_email)
    )

    assert admin_account is not None
    assert admin_account.role == UserRole.ADMIN
    assert verify_plain_password(settings.seed_admin_password, admin_account.hashed_password)

    assert agent_account is not None
    assert agent_account.role == UserRole.AGENT
    assert verify_plain_password(settings.seed_agent_password, agent_account.hashed_password)


def test_seed_is_idempotent(database_session: Session) -> None:
    settings = get_application_settings()
    seed_default_staff_accounts(database_session, settings)
    seed_default_staff_accounts(database_session, settings)

    staff_count = len(
        database_session.scalars(
            select(UserAccount).where(
                UserAccount.email.in_([settings.seed_admin_email, settings.seed_agent_email])
            )
        ).all()
    )
    assert staff_count == 2


def test_register_client_saves_email_full_name_password(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    response = api_test_client.post(
        "/auth/register",
        json={
            "email": "Client.User@Example.com",
            "full_name": "Иван Иванов",
            "password": "ClientPass123",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"
    assert payload["user_account"]["email"] == "client.user@example.com"
    assert payload["user_account"]["full_name"] == "Иван Иванов"
    assert payload["user_account"]["role"] == "client"
    assert "hashed_password" not in payload["user_account"]

    saved_client = database_session.scalar(
        select(UserAccount).where(UserAccount.email == "client.user@example.com")
    )
    assert saved_client is not None
    assert verify_plain_password("ClientPass123", saved_client.hashed_password)


def test_register_duplicate_email_returns_400(api_test_client: TestClient) -> None:
    body = {
        "email": "dup@example.com",
        "full_name": "First",
        "password": "ClientPass123",
    }
    first_response = api_test_client.post("/auth/register", json=body)
    second_response = api_test_client.post("/auth/register", json=body)

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Email is already registered"


def test_login_client_after_register(api_test_client: TestClient) -> None:
    api_test_client.post(
        "/auth/register",
        json={
            "email": "login.client@example.com",
            "full_name": "Login Client",
            "password": "ClientPass123",
        },
    )
    response = api_test_client.post(
        "/auth/login",
        json={
            "email": "login.client@example.com",
            "password": "ClientPass123",
        },
    )

    assert response.status_code == 200
    assert response.json()["user_account"]["role"] == "client"


def test_login_admin_and_agent_after_seed(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    settings = get_application_settings()
    seed_default_staff_accounts(database_session, settings)

    admin_response = api_test_client.post(
        "/auth/login",
        json={
            "email": settings.seed_admin_email,
            "password": settings.seed_admin_password,
        },
    )
    agent_response = api_test_client.post(
        "/auth/login",
        json={
            "email": settings.seed_agent_email,
            "password": settings.seed_agent_password,
        },
    )

    assert admin_response.status_code == 200
    assert admin_response.json()["user_account"]["role"] == "admin"
    assert agent_response.status_code == 200
    assert agent_response.json()["user_account"]["role"] == "agent"


def test_login_wrong_password_returns_401(api_test_client: TestClient) -> None:
    api_test_client.post(
        "/auth/register",
        json={
            "email": "wrong.pass@example.com",
            "full_name": "Wrong Pass",
            "password": "ClientPass123",
        },
    )
    response = api_test_client.post(
        "/auth/login",
        json={
            "email": "wrong.pass@example.com",
            "password": "NotThePassword",
        },
    )
    assert response.status_code == 401


def test_me_requires_token(api_test_client: TestClient) -> None:
    response = api_test_client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(api_test_client: TestClient) -> None:
    register_response = api_test_client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "full_name": "Me User",
            "password": "ClientPass123",
        },
    )
    access_token = register_response.json()["access_token"]

    response = api_test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
    assert response.json()["full_name"] == "Me User"


def test_inactive_user_cannot_login(database_session: Session, api_test_client: TestClient) -> None:
    client_account = register_client_account(
        database_session,
        email="inactive@example.com",
        full_name="Inactive User",
        plain_password="ClientPass123",
    )
    client_account.is_active = False
    database_session.commit()

    response = api_test_client.post(
        "/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "ClientPass123",
        },
    )
    assert response.status_code == 403
