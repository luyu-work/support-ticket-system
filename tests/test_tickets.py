"""Tests for creating and listing support tickets."""

from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import SupportTicket, TicketStatus


def _register_client(api_test_client: TestClient, email: str = "ticket.client@example.com") -> str:
    response = api_test_client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Ticket Client",
            "password": "ClientPass123",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_problem_reasons_list(api_test_client: TestClient) -> None:
    response = api_test_client.get("/tickets/problem-reasons")
    assert response.status_code == 200
    reasons = response.json()
    values = {item["value"] for item in reasons}
    assert "login_issue" in values
    assert "other" in values


def test_client_creates_ticket_without_photos(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    access_token = _register_client(api_test_client)

    response = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {access_token}"},
        data={
            "problem_reason": "login_issue",
            "description": "Не могу войти после смены пароля",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "in_queue"
    assert payload["problem_reason"] == "login_issue"
    assert payload["title"] == "Проблема со входом"
    assert payload["problem_reason"] == "login_issue"
    assert payload["attachments"] == []

    saved = database_session.get(SupportTicket, payload["support_ticket_id"])
    assert saved is not None
    assert saved.status == TicketStatus.IN_QUEUE


def test_client_creates_ticket_with_photo(api_test_client: TestClient) -> None:
    access_token = _register_client(api_test_client, email="photo.client@example.com")
    photo_bytes = b"\x89PNG\r\n\x1a\n" + b"fake-png-content"

    response = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {access_token}"},
        data={
            "problem_reason": "bug_report",
            "description": "Кнопка не работает, скрин во вложении",
        },
        files=[
            ("photos", ("screen.png", BytesIO(photo_bytes), "image/png")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert len(payload["attachments"]) == 1
    assert payload["attachments"][0]["original_file_name"] == "screen.png"


def test_create_ticket_requires_auth(api_test_client: TestClient) -> None:
    response = api_test_client.post(
        "/tickets",
        data={
            "problem_reason": "other",
            "description": "test",
        },
    )
    assert response.status_code == 401


def test_agent_cannot_create_ticket(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    from app.core.settings import get_application_settings
    from app.services.seed_staff_accounts import seed_default_staff_accounts

    settings = get_application_settings()
    seed_default_staff_accounts(database_session, settings)

    login = api_test_client.post(
        "/auth/login",
        json={
            "email": settings.seed_agent_email,
            "password": settings.seed_agent_password,
        },
    )
    access_token = login.json()["access_token"]

    response = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {access_token}"},
        data={
            "problem_reason": "other",
            "description": "agent should not create",
        },
    )
    assert response.status_code == 403


def test_list_my_tickets(api_test_client: TestClient) -> None:
    access_token = _register_client(api_test_client, email="list.client@example.com")
    headers = {"Authorization": f"Bearer {access_token}"}

    api_test_client.post(
        "/tickets",
        headers=headers,
        data={"problem_reason": "other", "description": "first"},
    )
    api_test_client.post(
        "/tickets",
        headers=headers,
        data={"problem_reason": "payment_issue", "description": "second"},
    )

    response = api_test_client.get("/tickets/my", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_ticket_count"] == 2
    assert len(payload["items"]) == 2


def test_unknown_problem_reason_returns_400(api_test_client: TestClient) -> None:
    access_token = _register_client(api_test_client, email="bad.reason@example.com")
    response = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {access_token}"},
        data={
            "problem_reason": "not_a_real_reason",
            "description": "test",
        },
    )
    assert response.status_code == 400


def test_new_ticket_page_available(api_test_client: TestClient) -> None:
    response = api_test_client.get("/tickets/new")
    assert response.status_code == 200
    assert 'id="new-ticket-form"' in response.text


def test_my_tickets_page_available(api_test_client: TestClient) -> None:
    response = api_test_client.get("/tickets")
    assert response.status_code == 200
    assert "Мои тикеты" in response.text
    assert "Обратная связь" in response.text
    assert 'id="my-tickets-list"' in response.text


def test_problem_reason_labels_match_product(api_test_client: TestClient) -> None:
    response = api_test_client.get("/tickets/problem-reasons")
    labels = {item["value"]: item["label_ru"] for item in response.json()}
    assert labels["bug_report"] == "Баги"
    assert labels["payment_issue"] == "Проблема с оплатой"
    assert labels["feature_request"] == "Предложения по улучшению"
    assert labels["login_issue"] == "Проблема со входом"
    assert labels["other"] == "Другое"
