from sqlalchemy import Uuid

from operations_automation_hub.models.base import Base
from operations_automation_hub.models.request import RequestModel

table = RequestModel.__table__


def test_request_model_has_requests_tablename():
    assert RequestModel.__tablename__ == "requests"


def test_request_model_is_registered_in_base_metadata():
    assert "requests" in Base.metadata.tables


def test_request_model_has_expected_columns():
    assert set(table.columns.keys()) == {
        "request_id",
        "external_request_id",
        "client_name",
        "phone",
        "email",
        "inn",
        "product_type",
        "amount",
        "created_at",
        "status",
        "job_id",
    }


def test_request_model_has_expected_column_constraints():
    assert table.c.request_id.primary_key is True
    assert table.c.external_request_id.unique is True
    assert table.c.amount.nullable is False
    assert table.c.amount.type.precision == 15
    assert table.c.amount.type.scale == 2
    assert table.c.status.nullable is False
    unique_columns = {column.name for column in table.columns if column.unique}
    assert unique_columns == {"external_request_id"}
    assert all(column.nullable is False for column in table.columns if column.name != "job_id")


def test_request_model_has_optional_job_reference():
    assert table.c.job_id.nullable is True
    assert isinstance(table.c.job_id.type, Uuid)
    assert table.c.job_id.type.as_uuid is True
    assert len(table.c.job_id.foreign_keys) == 1
    foreign_key = next(iter(table.c.job_id.foreign_keys))
    assert foreign_key.target_fullname == "jobs.job_id"
    assert foreign_key.constraint.name == "fk_requests_job_id_jobs"
    job_id_indexes = [
        index for index in table.indexes if [column.name for column in index.columns] == ["job_id"]
    ]
    assert len(job_id_indexes) == 1
    assert job_id_indexes[0].unique is False
