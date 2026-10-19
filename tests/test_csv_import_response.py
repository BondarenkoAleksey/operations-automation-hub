from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from operations_automation_hub.schemas.csv_import import CsvImportResponse, CsvValidationIssue
from operations_automation_hub.schemas.job import JobResponse, JobStatus


def test_csv_import_response_without_job():
    response = CsvImportResponse(job=None, imported_count=0)
    assert response.job is None
    assert response.imported_count == 0
    assert response.duplicate_request_ids == []
    assert response.issues == []
    assert response.existing_request_ids == []


def test_csv_import_response_with_details():
    job = JobResponse(
        job_id=UUID("00000000-0000-0000-0000-000000000001"),
        status=JobStatus.PENDING,
        created_at=datetime(2026, 10, 19, 12, 0, tzinfo=UTC),
    )
    issue = CsvValidationIssue(
        record_number=4,
        field="amount",
        message="Сумма должна быть больше нуля",
        error_type="greater_than",
    )
    response = CsvImportResponse(
        job=job,
        imported_count=2,
        duplicate_request_ids=["REQ-DUP-001"],
        existing_request_ids=["REQ-EXIST-001"],
        issues=[issue],
    )
    assert response.job == job
    assert response.job.job_id == job.job_id
    assert response.job.status == JobStatus.PENDING
    assert response.imported_count == 2
    assert response.duplicate_request_ids == ["REQ-DUP-001"]
    assert response.existing_request_ids == ["REQ-EXIST-001"]
    assert response.issues == [issue]
    assert response.issues[0].record_number == 4
    assert response.issues[0].field == "amount"


def test_csv_import_response_rejects_negative_imported_count():
    with pytest.raises(ValidationError) as exc_info:
        CsvImportResponse(job=None, imported_count=-1)
    assert any(
        error["loc"] == ("imported_count",) and error["type"] == "greater_than_equal"
        for error in exc_info.value.errors()
    )


@pytest.mark.parametrize(
    "payload, missing_fields",
    [
        ({}, {"job", "imported_count"}),
        ({"imported_count": 0}, {"job"}),
        ({"job": None}, {"imported_count"}),
    ],
)
def test_csv_import_response_requires_explicit_fields(payload, missing_fields):
    with pytest.raises(ValidationError) as exc_info:
        CsvImportResponse(**payload)
    actual_missing = {
        error["loc"][0] for error in exc_info.value.errors() if error["type"] == "missing"
    }
    assert actual_missing == missing_fields


def test_csv_import_response_lists_are_independent():
    issue = CsvValidationIssue(
        record_number=4,
        field="amount",
        message="Сумма должна быть больше нуля",
        error_type="greater_than",
    )
    first = CsvImportResponse(job=None, imported_count=0)
    second = CsvImportResponse(job=None, imported_count=0)

    first.issues.append(issue)
    first.duplicate_request_ids.append("REQ-DUP-001")
    first.existing_request_ids.append("REQ-EXIST-001")

    assert first.issues == [issue]
    assert first.duplicate_request_ids == ["REQ-DUP-001"]
    assert first.existing_request_ids == ["REQ-EXIST-001"]
    assert second.issues == []
    assert second.duplicate_request_ids == []
    assert second.existing_request_ids == []


def test_csv_import_response_serializes_to_json_compatible_data():
    job = JobResponse(
        job_id=UUID("00000000-0000-0000-0000-000000000001"),
        status=JobStatus.PENDING,
        created_at=datetime(2026, 10, 19, 12, 0, tzinfo=UTC),
    )
    issue = CsvValidationIssue(
        record_number=4,
        field="amount",
        message="Сумма должна быть больше нуля",
        error_type="greater_than",
    )
    response = CsvImportResponse(
        job=job,
        imported_count=2,
        issues=[issue],
        duplicate_request_ids=["REQ-DUP-001"],
        existing_request_ids=["REQ-EXIST-001"],
    )

    payload = response.model_dump(mode="json")

    assert set(payload.keys()) == {
        "job",
        "imported_count",
        "issues",
        "duplicate_request_ids",
        "existing_request_ids",
    }
    assert isinstance(payload["job"], dict)
    assert payload["job"]["job_id"] == "00000000-0000-0000-0000-000000000001"
    assert payload["job"]["status"] == "PENDING"
    assert isinstance(payload["job"]["created_at"], str)
    assert payload["imported_count"] == 2
    assert payload["issues"] == [
        {
            "record_number": 4,
            "field": "amount",
            "message": "Сумма должна быть больше нуля",
            "error_type": "greater_than",
        }
    ]
