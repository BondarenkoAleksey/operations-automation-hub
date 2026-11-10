from dataclasses import dataclass
from enum import StrEnum

from operations_automation_hub.schemas.request import RequestStatus


class DecisionReason(StrEnum):
    INVALID_INN = "INVALID_INN"


@dataclass(frozen=True)
class RequestDecision:
    status: RequestStatus
    reason: DecisionReason


def decide_request(*, inn_is_valid: bool) -> RequestDecision | None:
    if not inn_is_valid:
        return RequestDecision(
            status=RequestStatus.REJECTED,
            reason=DecisionReason.INVALID_INN,
        )

    return None
