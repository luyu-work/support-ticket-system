"""HTML auth pages are served and usable."""

from fastapi.testclient import TestClient


def test_login_page_is_available(api_test_client: TestClient) -> None:
    response = api_test_client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Вход" in response.text
    assert 'id="login-form"' in response.text


def test_register_page_is_available(api_test_client: TestClient) -> None:
    response = api_test_client.get("/register")
    assert response.status_code == 200
    assert 'id="register-form"' in response.text


def test_root_redirects_to_login(api_test_client: TestClient) -> None:
    response = api_test_client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_static_auth_css_is_available(api_test_client: TestClient) -> None:
    response = api_test_client.get("/static/css/auth.css")
    assert response.status_code == 200
    assert "auth-page" in response.text


def test_home_page_is_available(api_test_client: TestClient) -> None:
    response = api_test_client.get("/home")
    assert response.status_code == 200
    assert 'data-page="home"' in response.text
