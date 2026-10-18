from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.job import JobStatus
from operations_automation_hub.schemas.request import RequestCreate, RequestStatus
from operations_automation_hub.services.request_import_service import RequestImportService

pytestmark = pytest.mark.integration

FIXED_CREATED_AT = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


def make_request_create(external_request_id: str, amount: str = "125000.50") -> RequestCreate:
    return RequestCreate(
        external_request_id=external_request_id,
        client_name="Тест Тестович",
        phone="+79001234567",
        email="operator@example.test",
        inn="841827179762",
        product_type="CONSUMER_LOAN",
        amount=Decimal(amount),
        created_at=FIXED_CREATED_AT,
    )


def make_request_model(external_request_id: str) -> RequestModel:
    return RequestModel(
        request_id=uuid4(),
        external_request_id=external_request_id,
        client_name="Тест Тестович",
        phone="+79001234567",
        email="operator@example.test",
        inn="841827179762",
        product_type="CONSUMER_LOAN",
        amount=Decimal("125000.50"),
        created_at=FIXED_CREATED_AT,
        status=RequestStatus.NEW,
    )


def business_fields_snapshot(request_model: RequestModel) -> dict:
    return {
        "request_id": request_model.request_id,
        "external_request_id": request_model.external_request_id,
        "client_name": request_model.client_name,
        "phone": request_model.phone,
        "email": request_model.email,
        "inn": request_model.inn,
        "product_type": request_model.product_type,
        "amount": request_model.amount,
        "created_at": request_model.created_at,
        "status": request_model.status,
        "job_id": request_model.job_id,
    }


def count_jobs(session) -> int:
    return session.scalar(select(func.count()).select_from(JobModel))


def count_requests(session) -> int:
    return session.scalar(select(func.count()).select_from(RequestModel))


def test_import_requests_creates_job_and_linked_requests():
    with SessionLocal() as session:
        service = RequestImportService(session)
        job_repository = JobRepository(session)
        try:
            first = make_request_create(f"TEST-{uuid4()}")
            second = make_request_create(f"TEST-{uuid4()}")
            input_requests = [first, second]
            dumps_before = [r.model_dump() for r in input_requests]

            job = service.import_requests(input_requests)

            assert job is not None
            assert job.status == JobStatus.PENDING
            session.expunge_all()

            found_job = job_repository.get_by_id(job.job_id)
            assert found_job is not None
            assert found_job.status == JobStatus.PENDING
            assert found_job is not job

            rows = session.scalars(
                select(RequestModel).where(RequestModel.job_id == job.job_id)
            ).all()
            assert len(rows) == 2
            by_external_id = {row.external_request_id: row for row in rows}

            assert set(by_external_id) == {
                first.external_request_id,
                second.external_request_id,
            }
            for source in input_requests:
                saved = by_external_id[source.external_request_id]
                assert saved.status == RequestStatus.NEW
                assert saved.job_id == job.job_id
                assert saved.client_name == source.client_name
                assert saved.phone == source.phone
                assert saved.email == source.email
                assert saved.inn == source.inn
                assert saved.product_type == source.product_type
                assert saved.amount == source.amount
                assert saved.created_at == source.created_at

            assert [r.model_dump() for r in input_requests] == dumps_before
        finally:
            session.rollback()


def test_import_requests_with_empty_input_creates_no_job():
    with SessionLocal() as session:
        service = RequestImportService(session)
        try:
            count_before = count_jobs(session)

            result = service.import_requests([])

            count_after = count_jobs(session)
            assert result is None
            assert count_after == count_before
        finally:
            session.rollback()


def test_import_requests_skips_duplicates_and_existing_ids():
    with SessionLocal() as session:
        service = RequestImportService(session)
        request_repository = RequestRepository(session)
        try:
            id_a = f"TEST-{uuid4()}"
            existing_a = make_request_model(id_a)
            request_repository.create(existing_a)
            snapshot_a = business_fields_snapshot(existing_a)

            id_b = f"TEST-{uuid4()}"
            id_c = f"TEST-{uuid4()}"
            input_requests = [
                make_request_create(id_b, amount="100.00"),
                make_request_create(id_b, amount="200.00"),
                make_request_create(id_a),
                make_request_create(id_c),
            ]
            dumps_before = [r.model_dump() for r in input_requests]

            job = service.import_requests(input_requests)

            assert job is not None
            rows = session.scalars(
                select(RequestModel).where(RequestModel.job_id == job.job_id)
            ).all()
            assert [row.external_request_id for row in rows] == [id_c]

            b_rows = session.scalars(
                select(RequestModel).where(RequestModel.external_request_id == id_b)
            ).all()
            assert b_rows == []

            session.expunge_all()
            found_a = request_repository.get_by_id(existing_a.request_id)
            assert found_a is not None
            assert business_fields_snapshot(found_a) == snapshot_a

            assert [r.model_dump() for r in input_requests] == dumps_before
        finally:
            session.rollback()


@pytest.mark.parametrize("case", ["duplicate-inside-input", "already-exists"])
def test_import_requests_with_only_skipped_records_creates_nothing(case):
    with SessionLocal() as session:
        service = RequestImportService(session)
        request_repository = RequestRepository(session)
        try:
            if case == "already-exists":
                existing = make_request_model(f"TEST-{uuid4()}")
                request_repository.create(existing)
                input_requests = [make_request_create(existing.external_request_id)]
            else:
                duplicated_id = f"TEST-{uuid4()}"
                input_requests = [
                    make_request_create(duplicated_id),
                    make_request_create(duplicated_id),
                ]

            jobs_before = count_jobs(session)
            requests_before = count_requests(session)

            result = service.import_requests(input_requests)

            assert result is None
            assert count_jobs(session) == jobs_before
            assert count_requests(session) == requests_before
        finally:
            session.rollback()


def test_import_requests_rolls_back_job_and_requests_together():
    with SessionLocal() as session:
        service = RequestImportService(session)
        try:
            first = make_request_create(f"TEST-{uuid4()}")
            second = make_request_create(f"TEST-{uuid4()}")

            job = service.import_requests([first, second])

            assert job is not None
            job_id_value = job.job_id
            rows = session.scalars(
                select(RequestModel).where(RequestModel.job_id == job_id_value)
            ).all()
            assert len(rows) == 2
            saved_request_ids = {row.request_id for row in rows}

            session.rollback()

            assert (
                session.scalar(
                    select(func.count())
                    .select_from(JobModel)
                    .where(JobModel.job_id == job_id_value)
                )
                == 0
            )
            remaining = session.scalar(
                select(func.count())
                .select_from(RequestModel)
                .where(RequestModel.request_id.in_(saved_request_ids))
            )
            assert remaining == 0
        finally:
            session.rollback()


def test_import_requests_can_be_rolled_back_after_partial_failure(monkeypatch):
    original_create = RequestRepository.create
    calls = {"count": 0}

    def create_wrapper(self, request):
        calls["count"] += 1
        if calls["count"] == 1:
            return original_create(self, request)
        raise RuntimeError("Simulated request creation failure")

    monkeypatch.setattr(RequestRepository, "create", create_wrapper)
    with SessionLocal() as session:
        service = RequestImportService(session)
        try:
            first_id = f"TEST-{uuid4()}"
            second_id = f"TEST-{uuid4()}"
            input_requests = [
                make_request_create(first_id),
                make_request_create(second_id),
            ]
            with pytest.raises(RuntimeError, match="Simulated request creation failure"):
                service.import_requests(input_requests)
            assert calls["count"] == 2
            first_row = session.scalars(
                select(RequestModel).where(RequestModel.external_request_id == first_id)
            ).one()
            assert first_row.job_id is not None
            job_id_value = first_row.job_id
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(JobModel)
                    .where(JobModel.job_id == job_id_value)
                )
                == 1
            )
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(RequestModel)
                    .where(RequestModel.external_request_id == second_id)
                )
                == 0
            )
            session.rollback()
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(JobModel)
                    .where(JobModel.job_id == job_id_value)
                )
                == 0
            )
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(RequestModel)
                    .where(RequestModel.external_request_id.in_([first_id, second_id]))
                )
                == 0
            )
        finally:
            session.rollback()
