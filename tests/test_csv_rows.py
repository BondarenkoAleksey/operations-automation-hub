import pytest

from operations_automation_hub.importers.csv_rows import csv_row_to_dict


def header() -> list[str]:
    return [
        "external_request_id",
        "client_name",
        "phone",
        "email",
        "inn",
        "product_type",
        "amount",
        "created_at",
    ]


def row() -> list[str]:
    return [
        "REQ-001",
        "Иванов, Иван",
        "+79990000001",
        "",
        "000000000001",
        "LOAN",
        "125000.50",
        "2026-09-12",
    ]


def test_validate_csv_row():
    assert csv_row_to_dict(header(), row()) == {
        "external_request_id": "REQ-001",
        "client_name": "Иванов, Иван",
        "phone": "+79990000001",
        "email": "",
        "inn": "000000000001",
        "product_type": "LOAN",
        "amount": "125000.50",
        "created_at": "2026-09-12",
    }


def test_validate_csv_row_with_changed_columns():
    header = [
        "client_name",
        "external_request_id",
        "phone",
        "email",
        "inn",
        "product_type",
        "amount",
        "created_at",
    ]
    row = [
        "Иванов, Иван",
        "REQ-001",
        "+79990000001",
        "",
        "000000000001",
        "LOAN",
        "125000.50",
        "2026-09-12",
    ]
    assert csv_row_to_dict(header, row) == {
        "client_name": "Иванов, Иван",
        "external_request_id": "REQ-001",
        "phone": "+79990000001",
        "email": "",
        "inn": "000000000001",
        "product_type": "LOAN",
        "amount": "125000.50",
        "created_at": "2026-09-12",
    }


def test_validate_csv_row_with_missing_column():
    with pytest.raises(ValueError, match="shorter"):
        csv_row_to_dict(header(), row()[:-1])


def test_validate_csv_row_with_extra_column():
    with pytest.raises(ValueError, match="longer"):
        csv_row_to_dict(header(), row() + ["Moscow"])
