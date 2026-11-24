import os
from uuid import UUID

from celery import Celery

from operations_automation_hub.job_runner import run_job_decisions
from operations_automation_hub.services.request_decision import ScoringStatus

celery_app = Celery(
    "operations_automation_hub",
    broker=os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
)


@celery_app.task
def smoke_task():
    return "PONG"


@celery_app.task
def run_job_decisions_task(
    job_id: str,
    checks_by_request_id: dict[str, dict],
):
    job_uuid = UUID(job_id)

    restored_checks = {
        UUID(request_id): {
            "inn_is_valid": checks["inn_is_valid"],
            "risk_score": checks["risk_score"],
            "scoring_status": ScoringStatus(checks["scoring_status"]),
        }
        for request_id, checks in checks_by_request_id.items()
    }

    return run_job_decisions(
        job_id=job_uuid,
        checks_by_request_id=restored_checks,
    )
