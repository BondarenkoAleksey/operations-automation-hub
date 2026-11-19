from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.job import JobStatus
from operations_automation_hub.schemas.request import RequestStatus


@pytest.mark.integration
def test_create_and_get_request():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            request_id = uuid4()
            request = RequestModel(
                request_id=request_id,
                external_request_id=f"TEST-{uuid4()}",
                client_name="Тест Тестович",
                phone="+79001234567",
                email="mail@mail.com",
                inn="841827179762",
                product_type="тест_тип_продукта",
                amount=Decimal("125000.50"),
                created_at=datetime(year=2026, month=9, day=1, tzinfo=timezone.utc),
                status=RequestStatus.NEW,
            )
            repository.create(request)
            session.expunge_all()
            found = repository.get_by_id(request_id)
            assert found is not request
            assert found is not None
            assert found.request_id == request_id
            assert found.external_request_id == request.external_request_id
            assert found.client_name == request.client_name
            assert found.phone == request.phone
            assert found.email == request.email
            assert found.inn == request.inn
            assert found.product_type == request.product_type
            assert found.amount == request.amount
            assert found.created_at == request.created_at
            assert found.status == RequestStatus.NEW
            assert found.job_id is None
        finally:
            session.rollback()


@pytest.mark.integration
def test_get_by_id_returns_none_for_missing():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            random_id = uuid4()
            result = repository.get_by_id(random_id)
            assert result is None
        finally:
            session.rollback()


@pytest.mark.integration
def test_create_request_with_existing_job():
    with SessionLocal() as session:
        job_repository = JobRepository(session)
        request_repository = RequestRepository(session)
        try:
            job = JobModel(
                job_id=uuid4(),
                status=JobStatus.PENDING,
                created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
            )
            job_repository.create(job)

            request = RequestModel(
                request_id=uuid4(),
                external_request_id=f"TEST-{uuid4()}",
                client_name="Иван Петров",
                phone="+79991234567",
                email="ivan.petrov@example.test",
                inn="7707083893",
                product_type="CONSUMER_LOAN",
                amount=Decimal("125000.50"),
                created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
                status=RequestStatus.NEW,
                job_id=job.job_id,
            )
            request_repository.create(request)
            session.expunge_all()

            found = request_repository.get_by_id(request.request_id)
            assert found is not None
            assert found is not request
            assert found.job_id == job.job_id
        finally:
            session.rollback()


@pytest.mark.integration
def test_create_request_with_missing_job_raises_integrity_error():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            request = RequestModel(
                request_id=uuid4(),
                external_request_id=f"TEST-{uuid4()}",
                client_name="Иван Петров",
                phone="+79991234567",
                email="ivan.petrov@example.test",
                inn="7707083893",
                product_type="CONSUMER_LOAN",
                amount=Decimal("125000.50"),
                created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
                status=RequestStatus.NEW,
                job_id=uuid4(),
            )
            with pytest.raises(IntegrityError) as exc_info:
                repository.create(request)

            error = exc_info.value.orig
            assert error.sqlstate == "23503"
            assert error.diag.constraint_name == "fk_requests_job_id_jobs"
        finally:
            session.rollback()


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
def test_find_existing_external_request_ids_with_empty_input():
    ids = set()
    with SessionLocal() as session:
        repository = RequestRepository(session)
        result = repository.find_existing_external_request_ids(ids)
        assert result == set()
        assert isinstance(result, set)


@pytest.mark.integration
def test_find_existing_external_request_ids_without_matches():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            repository.create(make_request(external_request_id=f"TEST-{uuid4()}"))

            ids = {f"TEST-{uuid4()}", f"TEST-{uuid4()}"}
            result = repository.find_existing_external_request_ids(ids)

            assert result == set()
        finally:
            session.rollback()


@pytest.mark.integration
def test_find_existing_external_request_ids_returns_only_matches():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            external_request_id_a = f"TEST-{uuid4()}"
            external_request_id_b = f"TEST-{uuid4()}"
            external_request_id_c = f"TEST-{uuid4()}"

            repository.create(make_request(external_request_id=external_request_id_a))
            repository.create(make_request(external_request_id=external_request_id_b))
            repository.create(make_request(external_request_id=external_request_id_c))

            ids = {external_request_id_a, external_request_id_b, f"TEST-{uuid4()}"}
            ids_before = set(ids)

            result = repository.find_existing_external_request_ids(ids)

            assert result == {external_request_id_a, external_request_id_b}
            assert isinstance(result, set)
            assert ids == ids_before
        finally:
            session.rollback()


@pytest.mark.integration
def test_update_decision_updates_status_and_reason():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            request = make_request(external_request_id=f"TEST-{uuid4()}")
            repository.create(request)
            request_id = request.request_id
            assert request.status == RequestStatus.NEW
            assert request.decision_reason is None
            updated = repository.update_decision(
                request_id,
                status=RequestStatus.MANUAL_REVIEW,
                decision_reason="HIGH_AMOUNT",
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
        finally:
            session.rollback()


@pytest.mark.integration
def test_update_decision_returns_none_for_missing_request():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            request_id = uuid4()
            updated = repository.update_decision(
                request_id,
                status=RequestStatus.MANUAL_REVIEW,
                decision_reason="HIGH_AMOUNT",
            )
            assert updated is None

            found = repository.get_by_id(request_id)
            assert found is None
        finally:
            session.rollback()


@pytest.mark.integration
def test_update_decision_does_not_change_another_request():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            request_one = make_request(external_request_id=f"TEST-{uuid4()}")
            request_two = make_request(external_request_id=f"TEST-{uuid4()}")
            repository.create(request_one)
            request_id_one = request_one.request_id
            repository.create(request_two)
            request_id_two = request_two.request_id
            repository.update_decision(
                request_id_one,
                status=RequestStatus.MANUAL_REVIEW,
                decision_reason="HIGH_AMOUNT",
            )
            session.expunge_all()
            found_one = repository.get_by_id(request_id_one)
            found_two = repository.get_by_id(request_id_two)
            assert found_one is not None
            assert found_one.decision_reason == "HIGH_AMOUNT"
            assert found_one.status == RequestStatus.MANUAL_REVIEW
            assert found_two is not None
            assert found_two.decision_reason is None
            assert found_two.status == RequestStatus.NEW

        finally:
            session.rollback()


@pytest.mark.integration
def test_update_decision_preserves_other_request_fields():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            request = make_request(external_request_id=f"TEST-{uuid4()}")
            repository.create(request)
            request_id = request.request_id
            original_fields = {
                "external_request_id": request.external_request_id,
                "client_name": request.client_name,
                "phone": request.phone,
                "email": request.email,
                "inn": request.inn,
                "product_type": request.product_type,
                "amount": request.amount,
                "created_at": request.created_at,
                "job_id": request.job_id,
            }
            repository.update_decision(
                request_id,
                status=RequestStatus.MANUAL_REVIEW,
                decision_reason="HIGH_AMOUNT",
            )
            session.expunge_all()
            found = repository.get_by_id(request_id)
            assert found is not None
            assert found.request_id == request_id
            assert found.status == RequestStatus.MANUAL_REVIEW
            assert found.decision_reason == "HIGH_AMOUNT"
            for field_name, expected_value in original_fields.items():
                assert getattr(found, field_name) == expected_value, field_name

        finally:
            session.rollback()


@pytest.mark.integration
def test_list_by_job_id_returns_only_requests_for_that_job():
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

            request_a1 = make_request(f"TEST-{uuid4()}")
            request_a2 = make_request(f"TEST-{uuid4()}")
            request_b = make_request(f"TEST-{uuid4()}")
            request_without_job = make_request(f"TEST-{uuid4()}")

            request_a1.job_id = job_a.job_id
            request_a2.job_id = job_a.job_id
            request_b.job_id = job_b.job_id

            request_repository.create(request_a1)
            request_repository.create(request_a2)
            request_repository.create(request_b)
            request_repository.create(request_without_job)

            result = request_repository.list_by_job_id(job_a.job_id)

            assert {request.request_id for request in result} == {
                request_a1.request_id,
                request_a2.request_id,
            }

        finally:
            session.rollback()
