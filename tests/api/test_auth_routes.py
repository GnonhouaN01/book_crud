from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from src.auth import routes as auth_routes


def test_login_returns_access_and_refresh_tokens(client, monkeypatch):
    user = SimpleNamespace(
        uid=uuid4(),
        email="reader@example.com",
        password_hash="stored-hash",
    )
    tokens = iter(["access-token", "refresh-token"])
    monkeypatch.setattr(
        auth_routes.user_service,
        "get_user_by_email",
        AsyncMock(return_value=user),
    )
    monkeypatch.setattr(auth_routes, "verify_password", lambda *_: True)
    monkeypatch.setattr(
        auth_routes,
        "create_access_token",
        lambda **_: next(tokens),
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "valid-password"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-token"
    assert response.json()["refresh_token"] == "refresh-token"


def test_login_with_invalid_credentials_uses_custom_error(client, monkeypatch):
    monkeypatch.setattr(
        auth_routes.user_service,
        "get_user_by_email",
        AsyncMock(return_value=None),
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_signup_rejects_duplicate_email(client, monkeypatch):
    monkeypatch.setattr(
        auth_routes.user_service,
        "user_exists",
        AsyncMock(return_value=True),
    )

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "first_name": "Ari",
            "last_name": "Reader",
            "username": "ari",
            "email": "existing@example.com",
            "password": "safe-test-password",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "user_already_exists"
