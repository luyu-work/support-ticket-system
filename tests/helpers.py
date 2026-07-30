"""Общие хелперы для API-тестов (токены, регистрация клиента)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import get_application_settings
from app.services.seed_staff_accounts import seed_default_staff_accounts

def register_client(
    api_test_client: TestClient, email: str, *, password: str = "ClientPass123"
) -> str:
    """Регистрирует клиента и возвращает access_token."""
    response = api_test_client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Test Client",
            "password": password,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]

def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

def admin_token(api_test_client: TestClient, database_session: Session) -> str:
    settings = get_application_settings()
    seed_default_staff_accounts(database_session, settings)
    login = api_test_client.post(
        "/auth/login",
        json={
            "email": settings.seed_admin_email,
            "password": settings.seed_admin_password,
        },
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]

def agent_token(api_test_client: TestClient, database_session: Session) -> str:
    settings = get_application_settings()
    seed_default_staff_accounts(database_session, settings)
    login = api_test_client.post(
        "/auth/login",
        json={
            "email": settings.seed_agent_email,
            "password": settings.seed_agent_password,
        },
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]
