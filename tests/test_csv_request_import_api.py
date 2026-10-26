from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from operations_automation_hub.database import engine, get_db
from operations_automation_hub.main import app
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.request import RequestStatus

HEADER = "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n"

pytestmark = pytest.mark.integration


@pytest.fixture
def api_db(monkeypatch):
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                bind=connection,
                autoflush=False,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            ) as session:

                def override_get_db():
                    yield session

                monkeypatch.setitem(
                    app.dependency_overrides,
                    get_db,
                    override_get_db,
                )

                with TestClient(app) as client:
                    yield client, session
        finally:
            transaction.rollback()


def post_csv(client, content: bytes):
    return client.post(
        "/imports/csv",
        files={"file": ("requests.csv", content, "text/csv")},
    )


def test_csv_import_creates_job_and_requests(api_db):
    first_id = f"TEST-{uuid4()}"
    second_id = f"TEST-{uuid4()}"
    record_one = (
        f"{first_id},Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00\n"
    )
    record_two = (
        f"{second_id},Петр,+79990000003,petr@test.ru,7707083895,LOAN,99000.00,2026-07-12T15:20:00\n"
    )
    client, session = api_db
    content = (HEADER + record_one + record_two).encode("utf-8")
    response = post_csv(client, content)
    assert response.status_code == 200
    body = response.json()
    assert body["imported_count"] == 2
    assert body["job"]["status"] == "PENDING"
    assert body["issues"] == []
    assert body["duplicate_request_ids"] == []
    assert body["existing_request_ids"] == []
    job_id = UUID(body["job"]["job_id"])
    job_repository = JobRepository(session)
    found_job = job_repository.get_by_id(job_id)
    assert found_job is not None
    rows = session.scalars(select(RequestModel).where(RequestModel.job_id == job_id)).all()
    assert len(rows) == 2
    by_external_id = {row.external_request_id: row for row in rows}
    assert set(by_external_id) == {first_id, second_id}
    assert by_external_id[first_id].status == RequestStatus.NEW
    assert by_external_id[second_id].status == RequestStatus.NEW


def test_csv_import_saves_valid_record_and_reports_issue(api_db):
    valid_id = f"TEST-{uuid4()}"
    invalid_id = f"TEST-{uuid4()}"
    record_one = (
        f"{valid_id},Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00\n"
    )
    record_two = (
        f"{invalid_id},Петр,+79990000003,petr@test.ru,7707083895,LOAN,0.00,2026-07-12T15:20:00\n"
    )
    client, session = api_db
    content = (HEADER + record_one + record_two).encode("utf-8")
    response = post_csv(client, content)
    assert response.status_code == 200
    body = response.json()
    assert body["imported_count"] == 1
    assert len(body["issues"]) == 1
    assert body["issues"][0]["record_number"] == 3
    assert body["issues"][0]["field"] == "amount"
    assert body["issues"][0]["error_type"] == "greater_than"
    job_id = UUID(body["job"]["job_id"])
    job_repository = JobRepository(session)
    found_job = job_repository.get_by_id(job_id)
    assert found_job is not None
    rows = session.scalars(select(RequestModel).where(RequestModel.job_id == job_id)).all()
    assert len(rows) == 1
    by_external_id = {row.external_request_id: row for row in rows}
    assert set(by_external_id) == {valid_id}
    assert by_external_id[valid_id].status == RequestStatus.NEW
    assert invalid_id not in by_external_id
    invalid_count = session.scalar(
        select(func.count())
        .select_from(RequestModel)
        .where(RequestModel.external_request_id == invalid_id)
    )
    assert invalid_count == 0


def test_csv_import_header_only_creates_nothing(api_db):
    client, session = api_db
    jobs_before = session.scalar(select(func.count()).select_from(JobModel))
    requests_before = session.scalar(select(func.count()).select_from(RequestModel))
    content = HEADER.encode("utf-8")
    response = post_csv(client, content)
    assert response.status_code == 200
    body = response.json()
    assert body["job"] is None
    assert body["imported_count"] == 0
    assert body["duplicate_request_ids"] == []
    assert body["existing_request_ids"] == []
    assert body["issues"] == []
    assert session.scalar(select(func.count()).select_from(JobModel)) == jobs_before
    assert session.scalar(select(func.count()).select_from(RequestModel)) == requests_before


def make_request_model(external_request_id: str) -> RequestModel:
    return RequestModel(
        request_id=uuid4(),
        external_request_id=external_request_id,
        client_name="Тест Тестович",
        phone="+79990000001",
        email="operator@example.test",
        inn="7707083893",
        product_type="CONSUMER_LOAN",
        amount=Decimal("125000.50"),
        created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
        status=RequestStatus.NEW,
    )


def test_csv_import_reports_skipped_ids(api_db):
    existing_id = f"TEST-{uuid4()}"
    duplicated_id = f"TEST-{uuid4()}"
    fresh_id = f"TEST-{uuid4()}"

    client, session = api_db
    existing = make_request_model(existing_id)
    RequestRepository(session).create(existing)

    content = (
        HEADER + f"{existing_id},Тестовый клиент,+79990000001,operator@example.test,7707083893,"
        f"CONSUMER_LOAN,125000.50,2026-10-21T12:00:00\n"
        + f"{duplicated_id},Тестовый клиент,+79990000001,operator@example.test,7707083893,"
        f"CONSUMER_LOAN,100.00,2026-10-21T12:00:00\n"
        + f"{duplicated_id},Тестовый клиент,+79990000001,operator@example.test,7707083893,"
        f"CONSUMER_LOAN,200.00,2026-10-21T12:00:00\n"
        + f"{fresh_id},Тестовый клиент,+79990000001,operator@example.test,7707083893,"
        f"CONSUMER_LOAN,125000.50,2026-10-21T12:00:00\n"
    ).encode("utf-8")

    response = post_csv(client, content)

    assert response.status_code == 200
    body = response.json()
    assert body["imported_count"] == 1
    assert body["existing_request_ids"] == [existing_id]
    assert body["duplicate_request_ids"] == [duplicated_id]
    assert body["issues"] == []

    job_id = UUID(body["job"]["job_id"])
    rows = session.scalars(select(RequestModel).where(RequestModel.job_id == job_id)).all()
    assert [row.external_request_id for row in rows] == [fresh_id]

    session.refresh(existing)
    assert existing.job_id is None

    duplicated_rows = session.scalars(
        select(RequestModel).where(RequestModel.external_request_id == duplicated_id)
    ).all()
    assert duplicated_rows == []


def test_csv_import_rolls_back_after_partial_failure(api_db, monkeypatch):
    original_create = RequestRepository.create
    calls = {"count": 0}

    def create_wrapper(self, request):
        calls["count"] += 1
        if calls["count"] == 1:
            return original_create(self, request)
        raise RuntimeError("Simulated request creation failure")

    monkeypatch.setattr(RequestRepository, "create", create_wrapper)

    first_id = f"TEST-{uuid4()}"
    second_id = f"TEST-{uuid4()}"
    client, session = api_db

    jobs_before = session.scalar(select(func.count()).select_from(JobModel))
    requests_before = session.scalar(select(func.count()).select_from(RequestModel))

    content = (
        HEADER + f"{first_id},Тестовый клиент,+79990000001,operator@example.test,7707083893,"
        f"CONSUMER_LOAN,125000.50,2026-10-21T12:00:00\n"
        + f"{second_id},Тестовый клиент,+79990000001,operator@example.test,7707083893,"
        f"CONSUMER_LOAN,125000.50,2026-10-21T12:00:00\n"
    ).encode("utf-8")

    with pytest.raises(RuntimeError, match="Simulated request creation failure"):
        post_csv(client, content)

    assert calls["count"] == 2
    assert session.scalar(select(func.count()).select_from(JobModel)) == jobs_before
    assert session.scalar(select(func.count()).select_from(RequestModel)) == requests_before
    assert (
        session.scalar(
            select(func.count())
            .select_from(RequestModel)
            .where(RequestModel.external_request_id.in_([first_id, second_id]))
        )
        == 0
    )


def test_csv_import_rolls_back_when_commit_fails(api_db, monkeypatch):
    client, session = api_db

    def fail_commit():
        raise RuntimeError("Simulated commit failure")

    monkeypatch.setattr(session, "commit", fail_commit)

    new_id = f"TEST-{uuid4()}"

    jobs_before = session.scalar(select(func.count()).select_from(JobModel))
    requests_before = session.scalar(select(func.count()).select_from(RequestModel))

    content = (
        HEADER
        + f"{new_id},Тестовый клиент,+79990000001,operator@example.test,7707083893,CONSUMER_LOAN,"
        f"125000.50,2026-10-21T12:00:00\n"
    ).encode("utf-8")

    with pytest.raises(RuntimeError, match="Simulated commit failure"):
        post_csv(client, content)

    assert session.scalar(select(func.count()).select_from(JobModel)) == jobs_before
    assert session.scalar(select(func.count()).select_from(RequestModel)) == requests_before
    assert (
        session.scalar(
            select(func.count())
            .select_from(RequestModel)
            .where(RequestModel.external_request_id == new_id)
        )
        == 0
    )


def test_csv_import_invalid_encoding_creates_nothing(api_db):
    client, session = api_db
    jobs_before = session.scalar(select(func.count()).select_from(JobModel))
    requests_before = session.scalar(select(func.count()).select_from(RequestModel))
    response = post_csv(client, b"\xff\xfe")
    assert response.status_code == 400
    assert response.json()["detail"] == "CSV must be UTF-8 encoded"
    assert session.scalar(select(func.count()).select_from(JobModel)) == jobs_before
    assert session.scalar(select(func.count()).select_from(RequestModel)) == requests_before


def test_csv_import_missing_file_creates_nothing(api_db):
    client, session = api_db
    jobs_before = session.scalar(select(func.count()).select_from(JobModel))
    requests_before = session.scalar(select(func.count()).select_from(RequestModel))
    response = client.post("/imports/csv")
    assert response.status_code == 422
    assert any(item["loc"] == ["body", "file"] for item in response.json()["detail"])
    assert session.scalar(select(func.count()).select_from(JobModel)) == jobs_before
    assert session.scalar(select(func.count()).select_from(RequestModel)) == requests_before


def test_csv_import_oversized_file_creates_nothing(api_db):
    client, session = api_db
    jobs_before = session.scalar(select(func.count()).select_from(JobModel))
    requests_before = session.scalar(select(func.count()).select_from(RequestModel))
    content = b"a" * (1_048_576 + 1)
    response = post_csv(client, content)
    assert response.status_code == 413
    assert response.json()["detail"] == "CSV file is too large"
    assert session.scalar(select(func.count()).select_from(JobModel)) == jobs_before
    assert session.scalar(select(func.count()).select_from(RequestModel)) == requests_before


def test_csv_import_only_invalid_records_creates_nothing(api_db):
    client, session = api_db
    jobs_before = session.scalar(select(func.count()).select_from(JobModel))
    requests_before = session.scalar(select(func.count()).select_from(RequestModel))
    external_id = f"TEST-{uuid4()}"
    content = (
        HEADER + f"{external_id},Тестовый клиент,+79990000001,operator@example.test,"
        "7707083893,CONSUMER_LOAN,0.00,2026-10-25T12:00:00\n"
    ).encode("utf-8")
    response = post_csv(client, content)
    assert response.status_code == 200
    body = response.json()
    assert body["job"] is None
    assert body["imported_count"] == 0
    assert body["duplicate_request_ids"] == []
    assert body["existing_request_ids"] == []
    assert len(body["issues"]) == 1
    assert body["issues"][0]["record_number"] == 2
    assert body["issues"][0]["field"] == "amount"
    assert body["issues"][0]["error_type"] == "greater_than"
    assert session.scalar(select(func.count()).select_from(JobModel)) == jobs_before
    assert session.scalar(select(func.count()).select_from(RequestModel)) == requests_before


def test_csv_import_only_duplicates_creates_nothing(api_db):
    duplicated_id = f"TEST-{uuid4()}"
    record_one = (
        f"{duplicated_id},Иван,+79990000001,ivan@test.ru,7707083893,LOAN,"
        f"100.00,2026-09-12T10:30:00\n"
    )
    record_two = (
        f"{duplicated_id},Петр,+79990000003,petr@test.ru,7707083895,LOAN,"
        f"200.00,2026-07-12T15:20:00\n"
    )
    client, session = api_db
    jobs_before = session.scalar(select(func.count()).select_from(JobModel))
    requests_before = session.scalar(select(func.count()).select_from(RequestModel))
    content = (HEADER + record_one + record_two).encode("utf-8")
    response = post_csv(client, content)
    assert response.status_code == 200
    body = response.json()
    assert body["job"] is None
    assert body["imported_count"] == 0
    assert body["issues"] == []
    assert body["duplicate_request_ids"] == [duplicated_id]
    assert body["existing_request_ids"] == []
    assert session.scalar(select(func.count()).select_from(JobModel)) == jobs_before
    assert session.scalar(select(func.count()).select_from(RequestModel)) == requests_before
