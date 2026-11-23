import os

from celery import Celery

celery_app = Celery(
    "operations_automation_hub",
    broker=os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
)


@celery_app.task
def smoke_task():
    return "PONG"
