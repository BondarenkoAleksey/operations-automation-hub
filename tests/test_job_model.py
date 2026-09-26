from operations_automation_hub.models.base import Base
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.schemas.job import JobStatus

table = JobModel.__table__


def test_job_model_has_jobs_tablename():
    assert JobModel.__tablename__ == "jobs"


def test_job_model_is_registered_in_base_metadata():
    assert "jobs" in Base.metadata.tables


def test_job_model_has_expected_columns():
    assert set(table.columns.keys()) == {
        "job_id",
        "status",
        "created_at",
    }


def test_job_model_has_expected_column_constraints():
    assert table.c.job_id.primary_key is True
    assert table.c.job_id.nullable is False
    assert table.c.status.nullable is False
    assert table.c.created_at.nullable is False
    assert table.c.status.type.enum_class is JobStatus
    assert table.c.status.type.name == "job_status"
