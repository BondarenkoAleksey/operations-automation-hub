import pytest

from operations_automation_hub.importers.csv_rows import csv_row_to_dict, read_csv_records


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


def test_validate_csv_records(tmp_path):
    csv_file = tmp_path / "records.csv"
    csv_file.write_text(
        "created_at,external_request_id,client_name,phone,email,inn,product_type,amount\n"
        '2026-09-12,REQ-001,"Иванов, Иван",+79990000001,,000000000001,LOAN,125000.50\n'
        "2026-09-13,REQ-002,Мария,+79990000002,maria@test.ru,7707083893,LOAN,99000.00\n",
        encoding="utf-8",
    )
    records = read_csv_records(csv_file)
    assert records == [
        {
            "external_request_id": "REQ-001",
            "client_name": "Иванов, Иван",
            "phone": "+79990000001",
            "email": "",
            "inn": "000000000001",
            "product_type": "LOAN",
            "amount": "125000.50",
            "created_at": "2026-09-12",
        },
        {
            "external_request_id": "REQ-002",
            "client_name": "Мария",
            "phone": "+79990000002",
            "email": "maria@test.ru",
            "inn": "7707083893",
            "product_type": "LOAN",
            "amount": "99000.00",
            "created_at": "2026-09-13",
        },
    ]


def test_validate_csv_records_without_rows(tmp_path):
    csv_file = tmp_path / "header_only.csv"
    csv_file.write_text(
        "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n",
        encoding="utf-8",
    )
    records = read_csv_records(csv_file)
    assert records == []


def test_validate_csv_records_with_error_in_header(tmp_path):
    csv_file = tmp_path / "bad_header.csv"
    csv_file.write_text(
        "request_id,client_name,phone,email,inn,product_type,amount,created_at\n"
        'REQ-001,"Иванов, Иван",+79990000001,,000000000001,LOAN,125000.50,2026-09-12\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Не хватает столбцов"):
        read_csv_records(csv_file)


def test_validate_csv_records_with_error_in_order_three(tmp_path):
    csv_file = tmp_path / "extra_field.csv"
    csv_file.write_text(
        "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n"
        'REQ-001,"Иванов, Иван",+79990000001,,000000000001,LOAN,125000.50,2026-09-12\n'
        'REQ-002,"Петров, Петр",+79990000002,petr@petra.net,7707083893,LOAN,'
        "9999.99,2025-01-31,Smolensk\n",
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match=r"Запись 3: ожидалось 8 полей, получено 9\.",
    ):
        read_csv_records(csv_file)
