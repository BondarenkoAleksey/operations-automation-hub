from fastapi.testclient import TestClient

from operations_automation_hub.main import app

client = TestClient(app)


def test_root_returns_api_message():
    response = client.get("/")
    status_code = response.status_code
    assert status_code == 200, f"Ожидаемый код ответа 200, фактический {status_code}"
    response_json = response.json()
    expected_json = {"message": "Operations Automation Hub API"}
    assert response_json == expected_json, (
        f"Ожидаемое тело ответа {expected_json}, фактическое - {response_json}"
    )


def test_health_returns_ok_status():
    response = client.get("/health")
    status_code = response.status_code
    assert status_code == 200, f"Ожидаемый код ответа 200, фактический {status_code}"
    response_json = response.json()
    expected_json = {"status": "ok"}
    assert response_json == expected_json, (
        f"Ожидаемое тело ответа {expected_json}, фактическое - {response_json}"
    )
