"""UI уехал в Next.js — здесь только лёгкий smoke на health API."""

from fastapi.testclient import TestClient

def test_api_still_has_health(api_test_client: TestClient) -> None:
    response = api_test_client.get("/health")
    assert response.status_code == 200

def test_old_login_page_not_served_by_api(api_test_client: TestClient) -> None:
    response = api_test_client.get("/login")
    assert response.status_code == 404
