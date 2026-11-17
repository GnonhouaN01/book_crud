import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.errors import register_exception_handlers


def test_unknown_route_uses_standard_error_response_and_is_logged(client, caplog):
    caplog.set_level(logging.INFO, logger="bookly.requests")

    response = client.get("/route-that-does-not-exist?secret=not-logged")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
    assert "GET /route-that-does-not-exist 404 completed" in caplog.text
    assert "secret=not-logged" not in caplog.text


def test_unexpected_error_does_not_expose_internal_details():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/failure")
    async def failure():
        raise RuntimeError("database password must stay private")

    response = TestClient(app, raise_server_exceptions=False).get("/failure")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "database password" not in response.text
