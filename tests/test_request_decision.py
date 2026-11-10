from operations_automation_hub.schemas.request import RequestStatus
from operations_automation_hub.services.request_decision import (
    DecisionReason,
    RequestDecision,
    decide_request,
)


def test_decide_request_returns_none_when_inn_is_valid():
    assert decide_request(inn_is_valid=True) is None


def test_decide_request_rejects_when_inn_is_invalid():
    assert decide_request(inn_is_valid=False) == RequestDecision(
        status=RequestStatus.REJECTED,
        reason=DecisionReason.INVALID_INN,
    )
