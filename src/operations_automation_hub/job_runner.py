from uuid import UUID

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.services.job_decision_service import JobDecisionService


def run_job_decisions(
    job_id: UUID,
    checks_by_request_id: dict[UUID, dict],
) -> None:
    with SessionLocal() as session:
        try:
            job_decision_service = JobDecisionService(session)
            job_decision_service.apply_decisions(job_id, checks_by_request_id)
            session.commit()
        except Exception:
            session.rollback()
            raise
