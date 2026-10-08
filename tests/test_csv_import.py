from datetime import datetime
from decimal import Decimal

import pytest

from operations_automation_hub.importers.csv_import import validate_csv_file
from operations_automation_hub.schemas.csv_import import CsvValidationResult
from operations_automation_hub.schemas.request import RequestCreate


def test_validate_csv_file_with_two_errors(tmp_path):
    csv_file = tmp_path / "file.csv"
    csv_file.write_text(
        "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n"
        "REQ-001,Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00\n"
        "REQ-002,Мария,+79990000002,,7707083894,LOAN,0.00,2026-09-13T19:10:00\n"
        "REQ-003,Петр,+79990000003,petr@test.ru,7707083895,LOAN,99000.00,2026-07-12T15:20:00\n",
        encoding="utf-8",
    )
    result = validate_csv_file(csv_file)
    assert result.valid_records == [
        RequestCreate(
            external_request_id="REQ-001",
            client_name="Иван",
            phone="+79990000001",
            email="ivan@test.ru",
            inn="7707083893",
            product_type="LOAN",
            amount=Decimal("125000.50"),
            created_at=datetime(2026, 9, 12, 10, 30),
        ),
        RequestCreate(
            external_request_id="REQ-003",
            client_name="Петр",
            phone="+79990000003",
            email="petr@test.ru",
            inn="7707083895",
            product_type="LOAN",
            amount=Decimal("99000.00"),
            created_at=datetime(2026, 7, 12, 15, 20),
        ),
    ]
    assert len(result.issues) == 2
    pairs = {(i.field, i.error_type) for i in result.issues}
    assert pairs == {("email", "string_too_short"), ("amount", "greater_than")}
    assert all(i.record_number == 3 for i in result.issues)
    assert all(i.message for i in result.issues)
    assert result.duplicate_request_ids == []


def test_file_without_records(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text(
        "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n",
        encoding="utf-8",
    )
    assert validate_csv_file(csv_file) == CsvValidationResult(
        valid_records=[], issues=[], duplicate_request_ids=[]
    )


def test_validate_csv_file_with_extra_column(tmp_path):
    csv_file = tmp_path / "file.csv"
    csv_file.write_text(
        "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n"
        "REQ-001,Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00,Tokyo\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"Запись 2: ожидалось 8 полей, получено 9\."):
        validate_csv_file(csv_file)


def test_validate_csv_file_with_same_pairwise_rows(tmp_path):
    csv_file = tmp_path / "file.csv"
    csv_file.write_text(
        "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n"
        "REQ-003,Петр,+79990000003,petr@test.ru,7707083895,LOAN,99000.00,2026-07-12T15:20:00\n"
        "REQ-001,Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00\n"
        "REQ-003,Петр,+79990000003,petr@test.ru,7707083895,LOAN,99000.00,2026-07-12T15:20:00\n"
        "REQ-001,Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00\n",
        encoding="utf-8",
    )
    result = validate_csv_file(csv_file)
    assert result.valid_records == [
        RequestCreate(
            external_request_id="REQ-003",
            client_name="Петр",
            phone="+79990000003",
            email="petr@test.ru",
            inn="7707083895",
            product_type="LOAN",
            amount=Decimal("99000.00"),
            created_at=datetime(2026, 7, 12, 15, 20),
        ),
        RequestCreate(
            external_request_id="REQ-001",
            client_name="Иван",
            phone="+79990000001",
            email="ivan@test.ru",
            inn="7707083893",
            product_type="LOAN",
            amount=Decimal("125000.50"),
            created_at=datetime(2026, 9, 12, 10, 30),
        ),
        RequestCreate(
            external_request_id="REQ-003",
            client_name="Петр",
            phone="+79990000003",
            email="petr@test.ru",
            inn="7707083895",
            product_type="LOAN",
            amount=Decimal("99000.00"),
            created_at=datetime(2026, 7, 12, 15, 20),
        ),
        RequestCreate(
            external_request_id="REQ-001",
            client_name="Иван",
            phone="+79990000001",
            email="ivan@test.ru",
            inn="7707083893",
            product_type="LOAN",
            amount=Decimal("125000.50"),
            created_at=datetime(2026, 9, 12, 10, 30),
        ),
    ]
    assert result.issues == []
    assert result.duplicate_request_ids == ["REQ-001", "REQ-003"]


def test_validate_csv_file_with_same_ids(tmp_path):
    csv_file = tmp_path / "file.csv"
    csv_file.write_text(
        "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n"
        "REQ-001,Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00\n"
        "REQ-001,Петр,+79990000003,petr@test.ru,7707083895,LOAN,0.00,2026-07-12T15:20:00\n",
        encoding="utf-8",
    )
    result = validate_csv_file(csv_file)
    assert result.valid_records == [
        RequestCreate(
            external_request_id="REQ-001",
            client_name="Иван",
            phone="+79990000001",
            email="ivan@test.ru",
            inn="7707083893",
            product_type="LOAN",
            amount=Decimal("125000.50"),
            created_at=datetime(2026, 9, 12, 10, 30),
        ),
    ]
    assert result.duplicate_request_ids == []
    assert len(result.issues) == 1
    assert result.issues[0].record_number == 3
    pairs = {(i.field, i.error_type) for i in result.issues}
    assert pairs == {("amount", "greater_than")}
