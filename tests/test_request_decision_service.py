from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.models.job import JobModel  # noqa: F401
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.request import RequestStatus
from operations_automation_hub.services.request_decision import ScoringStatus
from operations_automation_hub.services.request_decision_service import RequestDecisionService


@pytest.mark.integration
def test_apply_decision_uses_saved_amount_and_persists_result():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        service = RequestDecisionService(session)

        request_id = uuid4()

        request = RequestModel(
            request_id=request_id,
            external_request_id=f"TEST-{uuid4()}",
            client_name="Test Client",
            phone="+79990000000",
            email="operator@example.test",
            inn="7701234567",
            product_type="CREDIT",
            amount=Decimal("500000.01"),
            created_at=datetime.now(timezone.utc),
            status=RequestStatus.NEW,
        )

        try:
            repository.create(request)

            updated = service.apply_decision(
                request_id,
                inn_is_valid=True,
                risk_score=10,
                scoring_status=ScoringStatus.APPROVED,
            )

            assert updated is not None
            assert updated.request_id == request_id
            assert updated.status == RequestStatus.MANUAL_REVIEW
            assert updated.decision_reason == "HIGH_AMOUNT"

            session.expunge_all()

            found = repository.get_by_id(request_id)

            assert found is not None
            assert found.request_id == request_id
            assert found.status == RequestStatus.MANUAL_REVIEW
            assert found.decision_reason == "HIGH_AMOUNT"
            assert found.amount == Decimal("500000.01")

        finally:
            session.rollback()
