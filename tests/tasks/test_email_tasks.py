from email.utils import parseaddr
from unittest.mock import AsyncMock

from src import celery_tasks


def test_send_email_task_delivers_message(monkeypatch):
    send_message = AsyncMock()
    monkeypatch.setattr(celery_tasks.mail, "send_message", send_message)

    celery_tasks.send_email.run(
        ["reader@example.com"],
        "Welcome",
        "<h1>Hello</h1>",
    )

    send_message.assert_awaited_once()
    message = send_message.await_args.args[0]
    assert parseaddr(str(message.recipients[0]))[1] == "reader@example.com"
    assert message.subject == "Welcome"
    assert message.body == "<h1>Hello</h1>"
