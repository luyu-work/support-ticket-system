from fastapi.testclient import TestClient

from app.main import ticket_system_application

test_client = TestClient(ticket_system_application)


def test_health_endpoint_returns_ok() -> None:
    response = test_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["application_name"] == "support-ticket-system"
