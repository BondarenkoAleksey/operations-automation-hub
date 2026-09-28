import pytest

from operations_automation_hub.importers.csv_header import read_csv_header, validate_csv_header


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


def test_read_csv_file(tmp_path):
    temp_file = tmp_path / "file.csv"
    temp_file.write_text(
        "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n",
        encoding="utf-8",
    )
    header = read_csv_header(path=temp_file)
    assert header == [
        "external_request_id",
        "client_name",
        "phone",
        "email",
        "inn",
        "product_type",
        "amount",
        "created_at",
    ]


def test_read_empty_csv(tmp_path):
    temp_file = tmp_path / "empty.csv"
    temp_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="Пустой заголовок"):
        read_csv_header(path=temp_file)


def test_read_with_missing_column(tmp_path):
    temp_file = tmp_path / "missing.csv"
    temp_file.write_text(
        "external_request_id,client_name,phone,email,product_type,amount,created_at\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="inn"):
        read_csv_header(path=temp_file)
