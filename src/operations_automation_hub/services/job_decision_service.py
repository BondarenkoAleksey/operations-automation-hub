from uuid import UUID

from sqlalchemy.orm import Session

from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.services.request_decision_service import RequestDecisionService


class JobDecisionService:
    def __init__(self, session: Session) -> None:
        self._request_repository = RequestRepository(session)
        self._decision_service = RequestDecisionService(session)

    def apply_decisions(
        self,
        job_id: UUID,
        checks_by_request_id: dict[UUID, dict],
    ) -> None:
        requests = self._request_repository.list_by_job_id(job_id)

        for request in requests:
            checks = checks_by_request_id[request.request_id]
            self._decision_service.apply_decision(
                request.request_id,
                inn_is_valid=checks["inn_is_valid"],
                risk_score=checks["risk_score"],
                scoring_status=checks["scoring_status"],
            )
