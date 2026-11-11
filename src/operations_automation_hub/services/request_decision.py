from dataclasses import dataclass
from enum import StrEnum

from operations_automation_hub.schemas.request import RequestStatus


class DecisionReason(StrEnum):
    INVALID_INN = "INVALID_INN"
    HIGH_RISK_SCORE = "HIGH_RISK_SCORE"


@dataclass(frozen=True)
class RequestDecision:
    status: RequestStatus
    reason: DecisionReason


def decide_request(
    *,
    inn_is_valid: bool,
    risk_score: int,
) -> RequestDecision | None:
    if not inn_is_valid:
        return RequestDecision(
            status=RequestStatus.REJECTED,
            reason=DecisionReason.INVALID_INN,
        )
    if risk_score >= 80:
        return RequestDecision(
            status=RequestStatus.MANUAL_REVIEW,
            reason=DecisionReason.HIGH_RISK_SCORE,
        )
    return None
