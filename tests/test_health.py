from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok(api_test_client: TestClient) -> None:
    response = api_test_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["application_name"] == "support-ticket-system"
