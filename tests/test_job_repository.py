from datetime import datetime, timezone
from uuid import uuid4

import pytest

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.schemas.job import JobStatus


@pytest.mark.integration
def test_create_and_get_job():
    with SessionLocal() as session:
        repository = JobRepository(session)
        try:
            job_id = uuid4()
            job = JobModel(
                job_id=job_id,
                created_at=datetime(year=2026, month=9, day=1, tzinfo=timezone.utc),
                status=JobStatus.PENDING,
            )
            created = repository.create(job)
            assert created is job
            session.expunge_all()

            found = repository.get_by_id(job_id)
            assert found is not None
            assert found is not job
            assert found.job_id == job_id
            assert found.created_at == job.created_at
            assert found.status == JobStatus.PENDING
        finally:
            session.rollback()


@pytest.mark.integration
def test_get_by_id_returns_none_for_missing_job():
    with SessionLocal() as session:
        repository = JobRepository(session)
        try:
            random_id = uuid4()
            result = repository.get_by_id(random_id)
            assert result is None
        finally:
            session.rollback()
