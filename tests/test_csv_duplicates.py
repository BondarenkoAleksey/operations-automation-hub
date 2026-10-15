from datetime import datetime
from decimal import Decimal

import pytest

from operations_automation_hub.importers.csv_duplicates import (
    exclude_duplicate_requests,
    find_duplicate_request_ids,
)
from operations_automation_hub.schemas.request import RequestCreate


def request_one():
    return RequestCreate(
        external_request_id="REQ-001",
        client_name="Иван",
        phone="+79990000001",
        email="ivan@test.ru",
        inn="7707083893",
        product_type="LOAN",
        amount=Decimal("125000.50"),
        created_at=datetime(2026, 9, 12, 10, 30),
    )


def request_two():
    return RequestCreate(
        external_request_id="REQ-003",
        client_name="Петр",
        phone="+79990000003",
        email="petr@test.ru",
        inn="7707083895",
        product_type="LOAN",
        amount=Decimal("99000.00"),
        created_at=datetime(2026, 7, 12, 15, 20),
    )


def request_three():
    return RequestCreate(
        external_request_id="REQ-004",
        client_name="Николай",
        phone="+79990000004",
        email="kolya@test.ru",
        inn="7707083897",
        product_type="LOAN",
        amount=Decimal("199000.00"),
        created_at=datetime(2026, 8, 19, 16, 50),
    )


@pytest.mark.parametrize(
    "requests, expected",
    [
        ([], set()),
        ([request_one(), request_two()], set()),
        ([request_one(), request_one()], {"REQ-001"}),
        ([request_one(), request_one(), request_one()], {"REQ-001"}),
        ([request_one(), request_two(), request_one(), request_two()], {"REQ-001", "REQ-003"}),
    ],
)
def test_find_duplicate_request_ids(requests, expected):
    ids_before = [r.external_request_id for r in requests]
    assert find_duplicate_request_ids(requests) == expected
    ids_after = [r.external_request_id for r in requests]
    assert ids_after == ids_before


@pytest.mark.parametrize(
    "requests, expected",
    [
        ([], []),
        ([request_one(), request_two(), request_three()], ["REQ-001", "REQ-003", "REQ-004"]),
        ([request_one(), request_one()], []),
        ([request_one(), request_one(), request_one()], []),
        ([request_two(), request_one(), request_three(), request_one()], ["REQ-003", "REQ-004"]),
        ([request_one(), request_two(), request_one(), request_two()], []),
    ],
)
def test_exclude_duplicate_requests(requests, expected):
    ids_before = [r.external_request_id for r in requests]
    dumps_before = [r.model_dump() for r in requests]
    result = exclude_duplicate_requests(requests)
    assert [r.external_request_id for r in result] == expected
    assert result is not requests
    assert [r.external_request_id for r in requests] == ids_before
    assert [r.model_dump() for r in requests] == dumps_before
    if result:
        expected_objects = [r for r in requests if r.external_request_id in expected]
        assert all(a is b for a, b in zip(result, expected_objects))


def test_exclude_duplicate_requests_with_same_id_and_different_data():
    first = request_one()
    duplicate = request_two()
    duplicate.external_request_id = "REQ-001"
    third = request_three()
    result = exclude_duplicate_requests([first, duplicate, third])
    assert result == [third]
    assert result[0] is third
