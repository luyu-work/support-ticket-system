"""Admin agent management (create / update / delete)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import get_application_settings
from app.services.seed_staff_accounts import seed_default_staff_accounts


def _admin_token(api_test_client: TestClient, database_session: Session) -> str:
    settings = get_application_settings()
    seed_default_staff_accounts(database_session, settings)
    login = api_test_client.post(
        "/auth/login",
        json={
            "email": settings.seed_admin_email,
            "password": settings.seed_admin_password,
        },
    )
    assert login.status_code == 200
    return login.json()["access_token"]


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


def test_admin_lists_and_creates_agent(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    admin_token = _admin_token(api_test_client, database_session)
    headers = {"Authorization": f"Bearer {admin_token}"}

    listed = api_test_client.get("/admin/agents", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total_count"] >= 1

    created = api_test_client.post(
        "/admin/agents",
        headers=headers,
        json={
            "full_name": "Новиков Пётр Иванович",
            "agent_number": 7,
            "password": "AgentPass7",
            "work_days": [0, 1, 2, 3, 4],
            "work_time_start": "10:00",
            "work_time_end": "19:00",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["agent_number"] == 7
    assert body["full_name"] == "Новиков Пётр Иванович"
    assert body["work_days"] == [0, 1, 2, 3, 4]
    assert body["work_time_start"] == "10:00"
    assert body["work_time_end"] == "19:00"
    assert body["agent_badge"] == "Агент #007"

    # New agent can log in with generated email
    login = api_test_client.post(
        "/auth/login",
        json={"email": body["email"], "password": "AgentPass7"},
    )
    assert login.status_code == 200
    assert login.json()["user_account"]["role"] == "agent"


def test_admin_updates_and_deletes_agent(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    admin_token = _admin_token(api_test_client, database_session)
    headers = {"Authorization": f"Bearer {admin_token}"}

    created = api_test_client.post(
        "/admin/agents",
        headers=headers,
        json={
            "full_name": "Временный Агент",
            "agent_number": 42,
            "password": "TempPass42",
            "work_days": [5, 6],
            "work_time_start": "12:00",
            "work_time_end": "20:00",
        },
    )
    agent_id = created.json()["user_account_id"]

    patched = api_test_client.patch(
        f"/admin/agents/{agent_id}",
        headers=headers,
        json={
            "full_name": "Агент Обновлённый",
            "work_days": [0, 2, 4],
            "work_time_start": "08:00",
            "work_time_end": "16:00",
        },
    )
    assert patched.status_code == 200
    assert patched.json()["full_name"] == "Агент Обновлённый"
    assert patched.json()["work_days"] == [0, 2, 4]

    deleted = api_test_client.delete(f"/admin/agents/{agent_id}", headers=headers)
    assert deleted.status_code == 204

    listed = api_test_client.get("/admin/agents", headers=headers)
    ids = {item["user_account_id"] for item in listed.json()["items"]}
    assert agent_id not in ids

    # Soft-deleted agent cannot log in
    login = api_test_client.post(
        "/auth/login",
        json={"email": created.json()["email"], "password": "TempPass42"},
    )
    assert login.status_code in {401, 403}


def test_agent_cannot_manage_agents(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    agent_token = _agent_token(api_test_client, database_session)
    response = api_test_client.get(
        "/admin/agents",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert response.status_code == 403


def test_duplicate_agent_number_rejected(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    admin_token = _admin_token(api_test_client, database_session)
    headers = {"Authorization": f"Bearer {admin_token}"}
    # seed agent is number 1
    response = api_test_client.post(
        "/admin/agents",
        headers=headers,
        json={
            "full_name": "Дубликат",
            "agent_number": 1,
            "password": "DupPass11",
            "work_days": [0, 1, 2, 3, 4],
            "work_time_start": "09:00",
            "work_time_end": "18:00",
        },
    )
    assert response.status_code == 400
