from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from operations_automation_hub.schemas.csv_import import CsvValidationIssue, CsvValidationResult
from operations_automation_hub.schemas.request import RequestCreate


def test_csv_validation_result():
    result = CsvValidationResult()
    assert result.valid_records == []
    assert result.issues == []


def test_independence_of_lists():
    result_one = CsvValidationResult()
    result_two = CsvValidationResult()
    result_one.issues.append(
        CsvValidationIssue(
            record_number=3,
            field="amount",
            message="Сумма должна быть больше нуля",
            error_type="greater_than",
        )
    )
    result_one.valid_records.append(
        RequestCreate(
            external_request_id="REQ-001",
            client_name="Иванов, Иван",
            phone="+79990000001",
            email="operator@example.test",
            inn="000000000001",
            product_type="LOAN",
            amount=Decimal("125000.50"),
            created_at=datetime(2026, 9, 12, 10, 30),
        )
    )
    assert result_two.issues == []
    assert result_two.valid_records == []
    assert result_one.issues == [
        CsvValidationIssue(
            record_number=3,
            field="amount",
            message="Сумма должна быть больше нуля",
            error_type="greater_than",
        ),
    ]
    assert len(result_one.valid_records) == 1
    assert result_one.issues[0].record_number == 3


def test_check_length_and_fields():
    valid_records = [
        RequestCreate(
            external_request_id="REQ-001",
            client_name="Иванов, Иван",
            phone="+79990000001",
            email="operator@example.test",
            inn="000000000001",
            product_type="LOAN",
            amount=Decimal("125000.50"),
            created_at=datetime(2026, 9, 12, 10, 30),
        )
    ]
    issues = [
        CsvValidationIssue(
            record_number=5,
            field="email",
            message="Поле email не может быть пустым",
            error_type="string_too_short",
        ),
        CsvValidationIssue(
            record_number=5,
            field="amount",
            message="Сумма должна быть больше нуля",
            error_type="greater_than",
        ),
    ]
    result = CsvValidationResult()
    result.issues.extend(issues)
    result.valid_records.extend(valid_records)
    assert len(result.issues) == 2
    assert len(result.valid_records) == 1
    assert result.issues[0].record_number == 5
    assert result.issues[1].record_number == 5
    assert result.issues[1].field == "amount"
    assert result.issues[0].field == "email"
    assert result.valid_records[0].email == "operator@example.test"


def test_invalid_record_number():
    with pytest.raises(ValidationError) as exc_info:
        CsvValidationIssue(
            record_number=1,
            field="email",
            message="Поле email не может быть пустым",
            error_type="string_too_short",
        )
    assert any(error["loc"] == ("record_number",) for error in exc_info.value.errors())


def test_duplicate_request_ids():
    result_one = CsvValidationResult()
    result_two = CsvValidationResult()
    assert result_one.duplicate_request_ids == []
    assert result_two.duplicate_request_ids == []
    result_one.duplicate_request_ids.append("REQ-001")
    assert result_two.duplicate_request_ids == []
