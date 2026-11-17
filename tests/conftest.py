import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


os.environ.update(
    {
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/book_crud_test",
        "JWT_SECRET": "test-only-secret-that-is-never-used-outside-tests",
        "JWT_ALGORITHM": "HS256",
        "REDIS_URL": "redis://localhost:6379/15",
        "CELERY_BROKER_URL": "memory://",
        "MAIL_USERNAME": "test",
        "MAIL_PASSWORD": "test",
        "MAIL_FROM": "noreply@example.com",
        "MAIL_PORT": "587",
        "MAIL_SERVER": "localhost",
        "MAIL_FROM_NAME": "Bookly Tests",
        "MAIL_STARTTLS": "true",
        "MAIL_SSL_TLS": "false",
        "USE_CREDENTIALS": "false",
        "VALIDATE_CERTS": "false",
        "DOMAIN": "example.com",
    }
)


@pytest.fixture
def client():
    from src import app
    from src.db.main import get_session

    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = lambda: object()
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


@pytest.fixture
def authenticate_as(client: TestClient):
    from src import app
    from src.auth.dependencies import get_current_user

    def authenticate(role: str = "user"):
        user = SimpleNamespace(
            uid=uuid4(),
            email="reader@example.com",
            role=role,
        )
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    return authenticate
