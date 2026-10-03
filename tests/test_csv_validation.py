from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from operations_automation_hub.importers.csv_validation import validate_csv_record
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
