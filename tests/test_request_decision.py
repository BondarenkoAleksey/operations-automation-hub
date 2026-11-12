import pytest

from operations_automation_hub.schemas.request import RequestStatus
from operations_automation_hub.services.request_decision import (
    DecisionReason,
    RequestDecision,
    ScoringStatus,
    decide_request,
)


@pytest.mark.parametrize(
    ("inn_is_valid", "risk_score", "scoring_status", "expected"),
    [
        (True, 79, ScoringStatus.APPROVED, None),
        (
            True,
            80,
            ScoringStatus.APPROVED,
            RequestDecision(
                status=RequestStatus.MANUAL_REVIEW,
                reason=DecisionReason.HIGH_RISK_SCORE,
            ),
        ),
        (
            True,
            81,
            ScoringStatus.APPROVED,
            RequestDecision(
                status=RequestStatus.MANUAL_REVIEW,
                reason=DecisionReason.HIGH_RISK_SCORE,
            ),
        ),
        (
            False,
            0,
            ScoringStatus.APPROVED,
            RequestDecision(
                status=RequestStatus.REJECTED,
                reason=DecisionReason.INVALID_INN,
            ),
        ),
        (
            False,
            95,
            ScoringStatus.APPROVED,
            RequestDecision(
                status=RequestStatus.REJECTED,
                reason=DecisionReason.INVALID_INN,
            ),
        ),
        (
            True,
            79,
            ScoringStatus.DECLINED,
            RequestDecision(
                status=RequestStatus.REJECTED,
                reason=DecisionReason.SCORING_DECLINED,
            ),
        ),
        (
            True,
            80,
            ScoringStatus.DECLINED,
            RequestDecision(
                status=RequestStatus.MANUAL_REVIEW,
                reason=DecisionReason.HIGH_RISK_SCORE,
            ),
        ),
        (
            False,
            95,
            ScoringStatus.DECLINED,
            RequestDecision(
                status=RequestStatus.REJECTED,
                reason=DecisionReason.INVALID_INN,
            ),
        ),
    ],
)
def test_decide_request(inn_is_valid, risk_score, scoring_status, expected):
    assert (
        decide_request(
            inn_is_valid=inn_is_valid,
            risk_score=risk_score,
            scoring_status=scoring_status,
        )
        == expected
    )
