"""Common ticket pool for agents."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import get_application_settings
from app.models import SupportTicket, TicketStatus
from app.services.seed_staff_accounts import seed_default_staff_accounts
from app.services.support_ticket_service import (
    IMPORTANT_AFTER_HOURS,
    promote_stale_queue_tickets_to_important,
)


def _register_client(api_test_client: TestClient, email: str) -> str:
    response = api_test_client.post(
        "/auth/register",
        json={
            "email": email,
            "full_name": "Pool Client",
            "password": "ClientPass123",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _agent_token(api_test_client: TestClient, database_session: Session) -> str:
    settings = get_application_settings()
    seed_default_staff_accounts(database_session, settings)
    login = api_test_client.post(
        "/auth/login",
        json={
            "email": settings.seed_agent_email,
            "password": settings.seed_agent_password,
        },
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_agent_sees_common_pool(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    client_token = _register_client(api_test_client, "pool.client@example.com")
    create = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {client_token}"},
        data={
            "problem_reason": "bug_report",
            "description": "Pool ticket body",
        },
    )
    assert create.status_code == 201

    agent_token = _agent_token(api_test_client, database_session)
    pool = api_test_client.get(
        "/tickets/pool",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert pool.status_code == 200
    payload = pool.json()
    assert payload["total_ticket_count"] >= 1
    ids = {item["support_ticket_id"] for item in payload["items"]}
    assert create.json()["support_ticket_id"] in ids


def test_client_cannot_access_pool(api_test_client: TestClient) -> None:
    client_token = _register_client(api_test_client, "no.pool@example.com")
    response = api_test_client.get(
        "/tickets/pool",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert response.status_code == 403


def test_closed_ticket_moves_to_archive(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    client_token = _register_client(api_test_client, "archive.client@example.com")
    create = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {client_token}"},
        data={"problem_reason": "other", "description": "will be archived"},
    )
    ticket_id = create.json()["support_ticket_id"]
    agent_token = _agent_token(api_test_client, database_session)
    headers = {"Authorization": f"Bearer {agent_token}"}

    api_test_client.post(f"/tickets/{ticket_id}/claim", headers=headers)
    close = api_test_client.post(
        f"/tickets/{ticket_id}/close",
        headers=headers,
        json={"comment_text": "Готово, в архив"},
    )
    assert close.status_code == 200

    pool = api_test_client.get("/tickets/pool", headers=headers)
    assert pool.status_code == 200
    pool_ids = {item["support_ticket_id"] for item in pool.json()["items"]}
    assert ticket_id not in pool_ids

    archive = api_test_client.get("/tickets/archive", headers=headers)
    assert archive.status_code == 200
    archive_ids = {item["support_ticket_id"] for item in archive.json()["items"]}
    assert ticket_id in archive_ids

    # Client cannot open archive
    client_archive = api_test_client.get(
        "/tickets/archive",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert client_archive.status_code == 403


def test_ticket_activity_log_and_agent_comment(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    client_token = _register_client(api_test_client, "log.client@example.com")
    create = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {client_token}"},
        data={"problem_reason": "bug_report", "description": "need history"},
    )
    ticket_id = create.json()["support_ticket_id"]
    # Client-facing create response must not expose activity log
    assert create.json().get("activity_log") == []

    agent_token = _agent_token(api_test_client, database_session)
    headers = {"Authorization": f"Bearer {agent_token}"}

    claim = api_test_client.post(f"/tickets/{ticket_id}/claim", headers=headers)
    assert claim.status_code == 200
    claim_types = [event["event_type"] for event in claim.json()["activity_log"]]
    assert "created" in claim_types
    assert "claimed" in claim_types

    close = api_test_client.post(
        f"/tickets/{ticket_id}/close",
        headers=headers,
        json={"comment_text": "Исправлено на стороне поддержки"},
    )
    assert close.status_code == 200
    body = close.json()
    event_types = [event["event_type"] for event in body["activity_log"]]
    assert event_types == ["created", "claimed", "closed"]
    assert len(body["comments"]) == 1
    assert body["comments"][0]["comment_text"] == "Исправлено на стороне поддержки"

    detail = api_test_client.get(f"/tickets/{ticket_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["comments"][0]["comment_text"] == "Исправлено на стороне поддержки"
    assert len(detail.json()["activity_log"]) == 3

    # Client sees comment but not activity log
    client_detail = api_test_client.get(
        f"/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert client_detail.status_code == 200
    client_body = client_detail.json()
    assert len(client_body["comments"]) == 1
    assert client_body["comments"][0]["comment_text"] == "Исправлено на стороне поддержки"
    assert client_body["activity_log"] == []


def test_agent_claims_ticket(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    client_token = _register_client(api_test_client, "claim.client@example.com")
    create = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {client_token}"},
        data={
            "problem_reason": "other",
            "description": "Please claim me",
        },
    )
    ticket_id = create.json()["support_ticket_id"]
    agent_token = _agent_token(api_test_client, database_session)

    claim = api_test_client.post(
        f"/tickets/{ticket_id}/claim",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert claim.status_code == 200
    body = claim.json()
    assert body["status"] == "in_progress"
    assert body["assigned_agent_id"] is not None


def test_agent_closes_and_transfers_ticket(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    client_token = _register_client(api_test_client, "resolve.client@example.com")
    create = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {client_token}"},
        data={"problem_reason": "other", "description": "resolve me"},
    )
    ticket_id = create.json()["support_ticket_id"]
    agent_token = _agent_token(api_test_client, database_session)
    headers = {"Authorization": f"Bearer {agent_token}"}

    claim = api_test_client.post(f"/tickets/{ticket_id}/claim", headers=headers)
    assert claim.status_code == 200

    transfer = api_test_client.post(
        f"/tickets/{ticket_id}/transfer-to-engineers",
        headers=headers,
    )
    assert transfer.status_code == 200
    assert transfer.json()["status"] == "transferred_to_engineers"

    create2 = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {client_token}"},
        data={"problem_reason": "bug_report", "description": "close me"},
    )
    ticket_id2 = create2.json()["support_ticket_id"]
    api_test_client.post(f"/tickets/{ticket_id2}/claim", headers=headers)
    close = api_test_client.post(
        f"/tickets/{ticket_id2}/close",
        headers=headers,
        json={"comment_text": "Проблема решена, клиенту ответили"},
    )
    assert close.status_code == 200
    assert close.json()["status"] == "closed"

    # Comment is required when closing
    create3 = api_test_client.post(
        "/tickets",
        headers={"Authorization": f"Bearer {client_token}"},
        data={"problem_reason": "other", "description": "need comment"},
    )
    ticket_id3 = create3.json()["support_ticket_id"]
    api_test_client.post(f"/tickets/{ticket_id3}/claim", headers=headers)
    close_no_comment = api_test_client.post(
        f"/tickets/{ticket_id3}/close",
        headers=headers,
        json={"comment_text": "   "},
    )
    assert close_no_comment.status_code in {403, 422}


def test_stale_queue_becomes_important(database_session: Session) -> None:
    from app.models import UserAccount, UserRole
    from app.core.security import hash_plain_password

    client = UserAccount(
        email="stale.client@example.com",
        full_name="Stale Client",
        hashed_password=hash_plain_password("ClientPass123"),
        role=UserRole.CLIENT,
    )
    database_session.add(client)
    database_session.commit()
    database_session.refresh(client)

    old_time = datetime.now(UTC) - timedelta(hours=IMPORTANT_AFTER_HOURS + 1)
    ticket = SupportTicket(
        title="Old",
        problem_reason="other",
        description="waiting too long",
        status=TicketStatus.IN_QUEUE,
        client_author_id=client.user_account_id,
        created_at=old_time,
        updated_at=old_time,
    )
    database_session.add(ticket)
    database_session.commit()
    database_session.refresh(ticket)

    updated = promote_stale_queue_tickets_to_important(database_session)
    assert updated >= 1
    database_session.refresh(ticket)
    assert ticket.status == TicketStatus.IMPORTANT
