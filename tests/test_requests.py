from uuid import UUID

from fastapi.testclient import TestClient

from operations_automation_hub.main import app


def get_valid_request_payload():
    return {
        "external_request_id": "REQ-10001",
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
