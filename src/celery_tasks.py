import asyncio

from aiosmtplib.errors import SMTPException
from celery.utils.log import get_task_logger
from fastapi_mail.errors import ConnectionErrors

from src.celery_app import celery_app
from src.email import create_message, mail


logger = get_task_logger(__name__)


@celery_app.task(
    autoretry_for=(ConnectionErrors, SMTPException),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_email(recipients: list[str], subject: str, body: str) -> None:
    message = create_message(
        recipients=recipients,
        subject=subject,
        body=body,
    )
    asyncio.run(mail.send_message(message))
    logger.info("Email sent to %d recipient(s)", len(recipients))
