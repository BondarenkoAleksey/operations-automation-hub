from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.main import app
from operations_automation_hub.models.request import RequestModel

pytestmark = pytest.mark.integration

TEST_EXTERNAL_REQUEST_ID_PREFIX = "TEST-REQ-"


@pytest.fixture(autouse=True)
def clear_test_db():
    with SessionLocal.begin() as session:
        session.execute(
            delete(RequestModel).where(
                RequestModel.external_request_id.like(f"{TEST_EXTERNAL_REQUEST_ID_PREFIX}%")
            )
        )
    yield
    with SessionLocal.begin() as session:
        session.execute(
            delete(RequestModel).where(
                RequestModel.external_request_id.like(f"{TEST_EXTERNAL_REQUEST_ID_PREFIX}%")
            )
        )


def get_valid_request_payload():
    return {
        "external_request_id": f"{TEST_EXTERNAL_REQUEST_ID_PREFIX}{uuid4()}",
        "client_name": "Иван Петров",
        "phone": "+79991234567",
        "email": "ivan.petrov@example.test",
        "inn": "7707083893",
        "product_type": "CONSUMER_LOAN",
        "amount": 125000.50,
        "created_at": "2026-09-12T10:30:00",
    }


client = TestClient(app)


def assert_status_code(response, expected_status_code):
    status_code = response.status_code
    assert status_code == expected_status_code, (
        f"Ожидаемый код ответа {expected_status_code}, фактический {status_code}"
    )


def test_request_create():
    payload = get_valid_request_payload()
    response = client.post("/requests", json=payload)
    assert_status_code(response, expected_status_code=201)
    response_json = response.json()
    assert response_json.get("external_request_id") == payload.get("external_request_id"), (
        response_json.get("external_request_id")
    )
    assert response_json.get("amount") == str(payload["amount"]), response_json.get("amount")
    assert response_json.get("inn") == payload.get("inn"), response_json.get("inn")
    request_id = UUID(response_json["request_id"])
    assert request_id.version == 4
    assert response_json.get("status") == "NEW"


def test_request_create_incorrect_inn():
    payload = get_valid_request_payload()
    payload["inn"] = "77070838930"
    response = client.post("/requests", json=payload)
    assert_status_code(response, expected_status_code=422)


def test_request_create_zero_or_minus_amount():
    payload = get_valid_request_payload()
    payload["amount"] = 0
    response = client.post("/requests", json=payload)
    assert_status_code(response, expected_status_code=422)

    payload["amount"] = -1
    response = client.post("/requests", json=payload)
    assert_status_code(response, expected_status_code=422)


def test_success_get_request():
    payload = get_valid_request_payload()
    response = client.post("/requests", json=payload)
    assert_status_code(response, expected_status_code=201)
    request_id = UUID(response.json()["request_id"])
    response = client.get(f"/requests/{request_id}")
    assert_status_code(response, expected_status_code=200)
    response_json = response.json()
    assert response_json.get("external_request_id") == payload.get("external_request_id"), (
        response_json.get("external_request_id")
    )
    assert response_json.get("request_id") == str(request_id), response_json.get("request_id")
    assert response_json.get("status") == "NEW"


def test_get_request_not_found():
    request_id = uuid4()
    response = client.get(f"/requests/{request_id}")
    assert_status_code(response, expected_status_code=404)
    assert response.json()["detail"] == "Request not found"


def test_request_create_email_longer_than_database_limit():
    payload = get_valid_request_payload()
    invalid_email = f"{'a' * 246}@test.com"
    assert len(invalid_email) == 255
    payload["email"] = invalid_email
    response = client.post("/requests", json=payload)
    assert_status_code(response, expected_status_code=422)


def test_duplicate_external_request_id_returns_409():
    payload = get_valid_request_payload()
    first_response = client.post("/requests", json=payload)
    assert_status_code(first_response, expected_status_code=201)
    request_id = first_response.json()["request_id"]

    duplicate_response = client.post("/requests", json=payload)
    assert_status_code(duplicate_response, expected_status_code=409)
    assert duplicate_response.json()["detail"] == (
        "Request with this external_request_id already exists"
    )

    get_response = client.get(f"/requests/{request_id}")
    assert_status_code(get_response, expected_status_code=200)
    assert get_response.json()["external_request_id"] == payload["external_request_id"]
