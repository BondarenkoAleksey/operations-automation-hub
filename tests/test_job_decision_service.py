from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.job import JobStatus
from operations_automation_hub.schemas.request import RequestStatus
from operations_automation_hub.services.job_decision_service import JobDecisionService
from operations_automation_hub.services.request_decision import ScoringStatus


def make_request(external_request_id: str) -> RequestModel:
    return RequestModel(
        request_id=uuid4(),
        external_request_id=external_request_id,
        client_name="Тест Тестович",
        phone="+79001234567",
        email="mail@mail.com",
        inn="841827179762",
        product_type="тест_тип_продукта",
        amount=Decimal("125000.50"),
        created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        status=RequestStatus.NEW,
    )


@pytest.mark.integration
def test_apply_decisions_updates_both_requests_in_job():
    with SessionLocal() as session:
        job_repository = JobRepository(session)
        request_repository = RequestRepository(session)
        try:
            job_a = JobModel(
                job_id=uuid4(),
                status=JobStatus.PENDING,
                created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
            )

            job_repository.create(job_a)

            request_a1 = make_request(f"TEST-{uuid4()}")
            request_a2 = make_request(f"TEST-{uuid4()}")
            request_a1.job_id = job_a.job_id
            request_a1.amount = Decimal("100.00")

            request_a2.job_id = job_a.job_id
            request_a2.amount = Decimal("500000.01")

            request_repository.create(request_a1)
            request_repository.create(request_a2)

            checks_by_request_id = {
                request_a1.request_id: {
                    "inn_is_valid": True,
                    "risk_score": 10,
                    "scoring_status": ScoringStatus.APPROVED,
                },
                request_a2.request_id: {
                    "inn_is_valid": True,
                    "risk_score": 10,
                    "scoring_status": ScoringStatus.APPROVED,
                },
            }
            service = JobDecisionService(session)
            service.apply_decisions(job_a.job_id, checks_by_request_id)
            updated_a1 = request_repository.get_by_id(request_a1.request_id)
            updated_a2 = request_repository.get_by_id(request_a2.request_id)

            assert updated_a1 is not None
            assert updated_a1.status == RequestStatus.APPROVED
            assert updated_a1.decision_reason == "AUTOMATIC_APPROVAL"

            assert updated_a2 is not None
            assert updated_a2.status == RequestStatus.MANUAL_REVIEW
            assert updated_a2.decision_reason == "HIGH_AMOUNT"
        finally:
            session.rollback()


@pytest.mark.integration
def test_apply_decisions_only_updates_requests_in_target_job():
    with SessionLocal() as session:
        job_repository = JobRepository(session)
        request_repository = RequestRepository(session)
        try:
            job_a = JobModel(
                job_id=uuid4(),
                status=JobStatus.PENDING,
                created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
            )
            job_b = JobModel(
                job_id=uuid4(),
                status=JobStatus.PENDING,
                created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
            )

            job_repository.create(job_a)
            job_repository.create(job_b)

            request_a = make_request(f"TEST-{uuid4()}")
            request_b = make_request(f"TEST-{uuid4()}")
            request_a.job_id = job_a.job_id
            request_a.amount = Decimal("100.00")
            request_repository.create(request_a)
            checks_by_request_id = {
                request_a.request_id: {
                    "inn_is_valid": True,
                    "risk_score": 10,
                    "scoring_status": ScoringStatus.APPROVED,
                },
            }
            request_b.job_id = job_b.job_id
            request_repository.create(request_b)
            service = JobDecisionService(session)
            service.apply_decisions(job_a.job_id, checks_by_request_id)
            updated_a = request_repository.get_by_id(request_a.request_id)
            updated_b = request_repository.get_by_id(request_b.request_id)

            assert updated_a is not None
            assert updated_a.status == RequestStatus.APPROVED
            assert updated_a.decision_reason == "AUTOMATIC_APPROVAL"

            assert updated_b is not None
            assert updated_b.status == RequestStatus.NEW

        finally:
            session.rollback()
