from types import SimpleNamespace
from unittest.mock import Mock

from kombu.exceptions import OperationalError

from src.auth import routes as auth_routes


def test_email_queue_requires_admin(client, authenticate_as, monkeypatch):
    authenticate_as("user")
    enqueue = Mock()
    monkeypatch.setattr(auth_routes.send_email, "delay", enqueue)

    response = client.post(
        "/api/v1/auth/send_mail",
        json={"addresses": ["reader@example.com"]},
    )

    assert response.status_code == 403
    enqueue.assert_not_called()


def test_email_route_queues_valid_message(client, authenticate_as, monkeypatch):
    authenticate_as("admin")
    enqueue = Mock(return_value=SimpleNamespace(id="task-123"))
    monkeypatch.setattr(auth_routes.send_email, "delay", enqueue)

    response = client.post(
        "/api/v1/auth/send_mail",
        json={"addresses": ["reader@example.com"]},
    )

    assert response.status_code == 202
    assert response.json()["task_id"] == "task-123"
    assert response.json()["message"] == "Email queued successfully"
    assert enqueue.call_args.kwargs["recipients"] == ["reader@example.com"]


def test_email_route_rejects_invalid_address(client, authenticate_as, monkeypatch):
    authenticate_as("admin")
    enqueue = Mock()
    monkeypatch.setattr(auth_routes.send_email, "delay", enqueue)

    response = client.post(
        "/api/v1/auth/send_mail",
        json={"addresses": ["not-an-email"]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    enqueue.assert_not_called()


def test_email_route_reports_unavailable_broker(client, authenticate_as, monkeypatch):
    authenticate_as("admin")
    monkeypatch.setattr(
        auth_routes.send_email,
        "delay",
        Mock(side_effect=OperationalError("broker unavailable")),
    )

    response = client.post(
        "/api/v1/auth/send_mail",
        json={"addresses": ["reader@example.com"]},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_unavailable"
