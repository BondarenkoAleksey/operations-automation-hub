import pytest

from operations_automation_hub.schemas.request import RequestStatus
from operations_automation_hub.services.request_decision import (
    DecisionReason,
    RequestDecision,
    decide_request,
)


@pytest.mark.parametrize(
    ("inn_is_valid", "risk_score", "expected"),
    [
        (True, 79, None),
        (
            True,
            80,
            RequestDecision(
                status=RequestStatus.MANUAL_REVIEW,
                reason=DecisionReason.HIGH_RISK_SCORE,
            ),
        ),
        (
            True,
            81,
            RequestDecision(
                status=RequestStatus.MANUAL_REVIEW,
                reason=DecisionReason.HIGH_RISK_SCORE,
            ),
        ),
        (
            False,
            0,
            RequestDecision(
                status=RequestStatus.REJECTED,
                reason=DecisionReason.INVALID_INN,
            ),
        ),
        (
            False,
            95,
            RequestDecision(
                status=RequestStatus.REJECTED,
                reason=DecisionReason.INVALID_INN,
            ),
        ),
    ],
)
def test_decide_request(inn_is_valid, risk_score, expected):
    assert (
        decide_request(
            inn_is_valid=inn_is_valid,
            risk_score=risk_score,
        )
        == expected
    )
