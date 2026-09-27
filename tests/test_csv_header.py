import pytest

from operations_automation_hub.importers.csv_header import validate_csv_header


def test_validate_csv_header():
    validate_csv_header(
        [
            "external_request_id",
            "client_name",
            "phone",
            "email",
            "inn",
            "product_type",
            "amount",
            "created_at",
        ]
    )


def test_validate_csv_header_with_different_order():
    validate_csv_header(
        [
            "created_at",
            "external_request_id",
            "client_name",
            "phone",
            "email",
            "inn",
            "product_type",
            "amount",
        ]
    )


def test_empty_file():
    with pytest.raises(ValueError):
        validate_csv_header([])


def test_duplicate_columns():
    with pytest.raises(ValueError, match="Дублирующиеся столбцы.*inn"):
        validate_csv_header(
            [
                "external_request_id",
                "client_name",
                "email",
                "inn",
                "inn",
                "product_type",
                "amount",
                "created_at",
            ]
        )


def test_unnecessary_columns():
    with pytest.raises(ValueError, match="address"):
        validate_csv_header(
            [
                "external_request_id",
                "client_name",
                "phone",
                "email",
                "address",
                "inn",
                "product_type",
                "amount",
                "created_at",
            ]
        )


def test_not_enough_columns():
    with pytest.raises(ValueError, match="inn"):
        validate_csv_header(
            [
                "external_request_id",
                "client_name",
                "phone",
                "email",
                "product_type",
                "amount",
                "created_at",
            ]
        )
