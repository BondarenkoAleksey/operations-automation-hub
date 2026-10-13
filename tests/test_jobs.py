from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.main import app
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.schemas.job import JobStatus

pytestmark = pytest.mark.integration

client = TestClient(app)


@pytest.fixture()
def saved_job():
    job_id = uuid4()
    job = JobModel(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    try:
        with SessionLocal.begin() as session:
            JobRepository(session).create(job)
        yield job
    finally:
        with SessionLocal.begin() as session:
            session.execute(delete(JobModel).where(JobModel.job_id == job_id))


def test_get_job_returns_saved_job(saved_job):
    job_id = saved_job.job_id
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"job_id", "status", "created_at"}
    assert data["job_id"] == str(job_id)
    assert data["status"] == "PENDING"
    parsed = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    assert parsed == saved_job.created_at


def test_get_job_not_found():
    job_id = uuid4()
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_get_job_invalid_id():
    response = client.get("/jobs/not-a-uuid")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item["loc"] == ["path", "job_id"] for item in detail)
