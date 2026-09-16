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
    assert all(column.nullable is False for column in table.columns)
