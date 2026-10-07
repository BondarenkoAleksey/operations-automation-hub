from datetime import datetime
from decimal import Decimal

import pytest

from operations_automation_hub.importers.csv_duplicates import find_duplicate_request_ids
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
