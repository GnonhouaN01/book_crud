from celery import Celery

from src.config import Config


celery_app = Celery(
    "book_crud",
    broker=Config.CELERY_BROKER_URL or Config.REDIS_URL,
    include=["src.celery_tasks"],
)

celery_app.conf.update(
    accept_content=["json"],
    enable_utc=True,
    result_serializer="json",
    task_ignore_result=True,
    task_serializer="json",
    timezone="UTC",
    broker_connection_retry_on_startup=True,
)
