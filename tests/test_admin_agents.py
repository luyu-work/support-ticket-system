"""Admin agent management (create / update / delete)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers import admin_token, agent_token, auth_headers


def test_admin_lists_and_creates_agent(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    headers = auth_headers(admin_token(api_test_client, database_session))

    listed = api_test_client.get("/admin/agents", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total_count"] >= 1

    created = api_test_client.post(
        "/admin/agents",
        headers=headers,
        json={
            "full_name": "Новиков Пётр Иванович",
            "agent_number": 7,
            "email": "novikov@example.com",
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
    assert body["email"] == "novikov@example.com"
    assert body["password"] == "AgentPass7"
    assert body["work_days"] == [0, 1, 2, 3, 4]
    assert body["work_time_start"] == "10:00"
    assert body["work_time_end"] == "19:00"
    assert body["agent_badge"] == "Агент #007"

    login = api_test_client.post(
        "/auth/login",
        json={"email": "novikov@example.com", "password": "AgentPass7"},
    )
    assert login.status_code == 200
    assert login.json()["user_account"]["role"] == "agent"


def test_admin_updates_and_deletes_agent(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    headers = auth_headers(admin_token(api_test_client, database_session))

    created = api_test_client.post(
        "/admin/agents",
        headers=headers,
        json={
            "full_name": "Временный Агент",
            "agent_number": 42,
            "email": "temp.agent@example.com",
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
            "email": "updated.agent@example.com",
            "password": "NewPass99",
            "work_days": [0, 2, 4],
            "work_time_start": "08:00",
            "work_time_end": "16:00",
        },
    )
    assert patched.status_code == 200
    assert patched.json()["full_name"] == "Агент Обновлённый"
    assert patched.json()["email"] == "updated.agent@example.com"
    assert patched.json()["password"] == "NewPass99"
    assert patched.json()["work_days"] == [0, 2, 4]

    deleted = api_test_client.delete(f"/admin/agents/{agent_id}", headers=headers)
    assert deleted.status_code == 204

    listed = api_test_client.get("/admin/agents", headers=headers)
    ids = {item["user_account_id"] for item in listed.json()["items"]}
    assert agent_id not in ids

    login = api_test_client.post(
        "/auth/login",
        json={"email": created.json()["email"], "password": "TempPass42"},
    )
    assert login.status_code in {401, 403}


def test_agent_cannot_manage_agents(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    response = api_test_client.get(
        "/admin/agents",
        headers=auth_headers(agent_token(api_test_client, database_session)),
    )
    assert response.status_code == 403


def test_duplicate_agent_number_rejected(
    api_test_client: TestClient,
    database_session: Session,
) -> None:
    headers = auth_headers(admin_token(api_test_client, database_session))
    response = api_test_client.post(
        "/admin/agents",
        headers=headers,
        json={
            "full_name": "Дубликат",
            "agent_number": 1,
            "email": "dup@example.com",
            "password": "DupPass11",
            "work_days": [0, 1, 2, 3, 4],
            "work_time_start": "09:00",
            "work_time_end": "18:00",
        },
    )
    assert response.status_code == 400
