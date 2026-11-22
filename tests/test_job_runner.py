from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.job_runner import run_job_decisions
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.job import JobStatus
from operations_automation_hub.schemas.request import RequestStatus
from operations_automation_hub.services.request_decision import ScoringStatus


def make_request(external_request_id: str, request_id: UUID) -> RequestModel:
    return RequestModel(
        request_id=request_id,
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
def test_run_job_decisions_persists_request_decision():
    job_id = uuid4()
    request_id = uuid4()
    try:
        with SessionLocal() as session:
            job_repository = JobRepository(session)
            request_repository = RequestRepository(session)
            job = JobModel(
                job_id=job_id,
                status=JobStatus.PENDING,
                created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
            )

            job_repository.create(job)

            request = make_request(
                external_request_id=f"TEST-{uuid4()}",
                request_id=request_id,
            )
            request.job_id = job_id
            request.amount = Decimal("100.00")
            request_repository.create(request)
            session.commit()

        checks_by_request_id = {
            request_id: {
                "inn_is_valid": True,
                "risk_score": 10,
                "scoring_status": ScoringStatus.APPROVED,
            },
        }
        run_job_decisions(job_id=job_id, checks_by_request_id=checks_by_request_id)

        with SessionLocal() as verify_session:
            updated_request = RequestRepository(verify_session).get_by_id(request_id)

            assert updated_request is not None
            assert updated_request.status == RequestStatus.APPROVED
            assert updated_request.decision_reason == "AUTOMATIC_APPROVAL"

    finally:
        with SessionLocal() as cleanup_session:
            cleanup_session.execute(
                delete(RequestModel).where(RequestModel.request_id == request_id)
            )
            cleanup_session.execute(delete(JobModel).where(JobModel.job_id == job_id))
            cleanup_session.commit()
