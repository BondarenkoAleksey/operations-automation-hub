from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from operations_automation_hub.importers.csv_validation import (
    validate_csv_record,
    validate_csv_records,
)
from operations_automation_hub.schemas.request import RequestCreate


def record() -> dict[str, str]:
    return {
        "external_request_id": "REQ-001",
        "client_name": "Иванов, Иван",
        "phone": "+79990000001",
        "email": "operator@example.test",
        "inn": "000000000001",
        "product_type": "LOAN",
        "amount": "125000.50",
        "created_at": "2026-09-12T10:30:00",
    }


def test_csv_record_validation():
    result = validate_csv_record(record())
    assert isinstance(result, RequestCreate)
    assert result.amount == Decimal("125000.50")
    assert result.created_at == datetime(2026, 9, 12, 10, 30)
    assert result.inn == "000000000001"


def test_csv_record_validation_with_zero_amount():
    test_record = record()
    test_record["amount"] = "0"
    with pytest.raises(ValidationError) as exc_info:
        validate_csv_record(test_record)
    assert any(error["loc"] == ("amount",) for error in exc_info.value.errors())


def test_csv_record_validation_with_amount_is_not_a_number():
    test_record = record()
    test_record["amount"] = "not_a_number"
    with pytest.raises(ValidationError) as exc_info:
        validate_csv_record(test_record)
    assert any(error["loc"] == ("amount",) for error in exc_info.value.errors())


def test_csv_record_validation_with_empty_email():
    test_record = record()
    test_record["email"] = ""
    with pytest.raises(ValidationError) as exc_info:
        validate_csv_record(test_record)
    assert any(error["loc"] == ("email",) for error in exc_info.value.errors())


def test_csv_record_validation_with_created_at_is_not_datetime():
    test_record = record()
    test_record["created_at"] = "20-09-2026T10:30:00"
    with pytest.raises(ValidationError) as exc_info:
        validate_csv_record(test_record)
    assert any(error["loc"] == ("created_at",) for error in exc_info.value.errors())


def test_validate_csv_empty_records():
    records = []
    result = validate_csv_records(records)
    assert result.valid_records == []
    assert result.issues == []


def test_csv_record_validation_with_valid_records():
    record_one = record()
    record_two = {
        "external_request_id": "REQ-002",
        "client_name": "Петров, Петр",
        "phone": "+79990000002",
        "email": "operator2@example.test",
        "inn": "000000000002",
        "product_type": "LOAN",
        "amount": "99000.50",
        "created_at": "2026-01-15T16:35:00",
    }
    records = [record_one, record_two]
    result = validate_csv_records(records)
    assert result.valid_records == [
        RequestCreate(
            external_request_id="REQ-001",
            client_name="Иванов, Иван",
            phone="+79990000001",
            email="operator@example.test",
            inn="000000000001",
            product_type="LOAN",
            amount=Decimal("125000.50"),
            created_at=datetime(2026, 9, 12, 10, 30),
        ),
        RequestCreate(
            external_request_id="REQ-002",
            client_name="Петров, Петр",
            phone="+79990000002",
            email="operator2@example.test",
            inn="000000000002",
            product_type="LOAN",
            amount=Decimal("99000.50"),
            created_at=datetime(2026, 1, 15, 16, 35),
        ),
    ]
    assert result.issues == []


def test_csv_record_validation_with_invalid_record_with_empty_email():
    record_one = record()
    record_two = {
        "external_request_id": "REQ-002",
        "client_name": "Петров, Петр",
        "phone": "+79990000002",
        "email": "",
        "inn": "000000000002",
        "product_type": "LOAN",
        "amount": "99000.50",
        "created_at": "2026-01-15T16:35:00",
    }
    record_three = {
        "external_request_id": "REQ-003",
        "client_name": "Васильев, Василий",
        "phone": "+79990000003",
        "email": "operator3@example.test",
        "inn": "000000000003",
        "product_type": "LOAN",
        "amount": "1000.00",
        "created_at": "2026-01-31T10:00:00",
    }
    records = [record_one, record_two, record_three]
    result = validate_csv_records(records)
    assert result.valid_records == [
        RequestCreate(
            external_request_id="REQ-001",
            client_name="Иванов, Иван",
            phone="+79990000001",
            email="operator@example.test",
            inn="000000000001",
            product_type="LOAN",
            amount=Decimal("125000.50"),
            created_at=datetime(2026, 9, 12, 10, 30),
        ),
        RequestCreate(
            external_request_id="REQ-003",
            client_name="Васильев, Василий",
            phone="+79990000003",
            email="operator3@example.test",
            inn="000000000003",
            product_type="LOAN",
            amount=Decimal("1000.00"),
            created_at=datetime(2026, 1, 31, 10, 0),
        ),
    ]
    assert len(result.issues) == 1
    assert result.issues[0].record_number == 3
    assert result.issues[0].field == "email"
    assert result.issues[0].error_type == "string_too_short"
    assert result.issues[0].message


def test_csv_record_validation_with_invalid_record_with_empty_email_and_zero_amount():
    record_one = {
        "external_request_id": "REQ-004",
        "client_name": "Львов, Лев",
        "phone": "+79990000004",
        "email": "",
        "inn": "000000000004",
        "product_type": "LOAN",
        "amount": "0.00",
        "created_at": "2026-01-01T19:55:00",
    }
    result = validate_csv_records([record_one])
    assert result.valid_records == []
    pairs = {(issue.field, issue.error_type) for issue in result.issues}
    assert pairs == {("email", "string_too_short"), ("amount", "greater_than")}
    assert all(issue.message for issue in result.issues)
    assert len(result.issues) == 2
    assert all(issue.record_number == 2 for issue in result.issues)
