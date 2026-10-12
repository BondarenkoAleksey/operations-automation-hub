from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from operations_automation_hub.models.job import JobModel
from operations_automation_hub.schemas.job import JobResponse, JobStatus


def test_valid_fields_in_schema():
    created_at = datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc)
    test_id = uuid4()
    job = JobResponse(job_id=test_id, status=JobStatus.PENDING, created_at=created_at)
    assert job.job_id == test_id
    assert job.status == JobStatus.PENDING
    assert job.created_at == created_at


@pytest.mark.parametrize(
    "status",
    [
        JobStatus.PENDING,
        JobStatus.FAILED,
        JobStatus.PROCESSING,
        JobStatus.SUCCESS,
        JobStatus.PARTIAL_SUCCESS,
    ],
)
def test_valid_status(status):
    created_at = datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc)
    job = JobResponse(
        job_id=uuid4(),
        status=status,
        created_at=created_at,
    )
    assert job.status == status


def test_job_response_from_job_model():
    created_at = datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc)
    test_job_id = uuid4()
    job = JobModel(
        job_id=test_job_id,
        status=JobStatus.PENDING,
        created_at=created_at,
    )
    result = JobResponse.model_validate(job)
    assert result.status == JobStatus.PENDING
    assert result.created_at == created_at
    assert result.job_id == test_job_id


@pytest.mark.parametrize("missing_field", ["job_id", "status", "created_at"])
def test_required_fields_in_schema(missing_field):
    data = {
        "job_id": uuid4(),
        "status": JobStatus.PENDING,
        "created_at": datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
    }
    del data[missing_field]
    with pytest.raises(ValidationError) as exc_info:
        JobResponse(**data)
    assert any(e["loc"] == (missing_field,) for e in exc_info.value.errors())


def test_invalid_status():
    with pytest.raises(ValidationError):
        JobResponse(
            job_id=uuid4(),
            status="NEW",
            created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
        )


def test_invalid_job_id():
    with pytest.raises(ValidationError):
        JobResponse(
            job_id="123",
            status=JobStatus.SUCCESS,
            created_at=datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc),
        )


def test_job_response_json_serialization():
    test_id = uuid4()
    created_at = datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc)
    job = JobResponse(job_id=test_id, status=JobStatus.PENDING, created_at=created_at)

    data = job.model_dump(mode="json")

    assert set(data.keys()) == {"job_id", "status", "created_at"}
    assert data["job_id"] == str(test_id)
    assert data["status"] == "PENDING"
    parsed = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    assert parsed == created_at
