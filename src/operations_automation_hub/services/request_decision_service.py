from uuid import UUID

from sqlalchemy.orm import Session

from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.services.request_decision import ScoringStatus, decide_request


class RequestDecisionService:
    def __init__(self, session: Session) -> None:
        self._request_repository = RequestRepository(session)

    def apply_decision(
        self,
        request_id: UUID,
        *,
        inn_is_valid: bool,
        risk_score: int,
        scoring_status: ScoringStatus,
    ) -> RequestModel | None:
        request = self._request_repository.get_by_id(request_id)

        if request is None:
            return None

        decision = decide_request(
            inn_is_valid=inn_is_valid,
            risk_score=risk_score,
            scoring_status=scoring_status,
            amount=request.amount,
        )

        return self._request_repository.update_decision(
            request_id=request_id,
            status=decision.status,
            decision_reason=decision.reason.value,
        )
