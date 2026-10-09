import csv

from fastapi.testclient import TestClient

from operations_automation_hub.main import app

client = TestClient(app)

HEADER = "external_request_id,client_name,phone,email,inn,product_type,amount,created_at\n"


def post_csv(content: bytes):
    return client.post(
        "/imports/csv/validate",
        files={"file": ("requests.csv", content, "text/csv")},
    )


def test_header_only_returns_empty_lists():
    response = post_csv(HEADER.encode("utf-8"))
    assert response.status_code == 200
    body = response.json()
    assert body["valid_records"] == []
    assert body["issues"] == []
    assert body["duplicate_request_ids"] == []


def test_with_two_valid_records_with_same_id():
    record_one = (
        "REQ-001,Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00\n"
    )
    record_two = (
        "REQ-001,Петр,+79990000003,petr@test.ru,7707083895,LOAN,99000.00,2026-07-12T15:20:00\n"
    )
    response = post_csv((HEADER + record_one + record_two).encode("utf-8"))
    assert response.status_code == 200
    body = response.json()
    assert len(body["valid_records"]) == 2  # обе сохранены
    assert body["valid_records"][0]["external_request_id"] == "REQ-001"
    assert body["valid_records"][1]["external_request_id"] == "REQ-001"
    assert body["duplicate_request_ids"] == ["REQ-001"]  # один раз, отсортирован
    assert body["issues"] == []
    assert [record["client_name"] for record in body["valid_records"]] == ["Иван", "Петр"]


def test_with_extra_field():
    record = (
        "REQ-001,Иван,+79990000001,ivan@test.ru,7707083893,"
        "LOAN,125000.50,2026-09-12T10:30:00,Tokyo\n"
    )
    response = post_csv((HEADER + record).encode("utf-8"))
    assert response.status_code == 400
    assert "Запись 2: ожидалось 8 полей, получено 9." in response.json()["detail"]


def test_missing_file_returns_422():
    response = client.post("/imports/csv/validate")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item["loc"] == ["body", "file"] for item in detail)


def test_with_wrong_encoding():
    response = post_csv(b"\xff\xfe")
    assert response.status_code == 400
    assert response.json()["detail"] == "CSV must be UTF-8 encoded"


def test_with_file_extra_size():
    content = HEADER.encode("utf-8") + b"a" * (1_048_577 - len(HEADER.encode("utf-8")))
    response = post_csv(content)
    assert response.status_code == 413
    assert response.json()["detail"] == "CSV file is too large"


def test_field_larger_than_limit_returns_400():
    original_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(64)
        long_name = "А" * 65
        content = (
            HEADER + f"REQ-001,{long_name},+79990000001,ivan@test.ru,"
            f"7707083893,LOAN,125000.50,2026-09-12T10:30:00\n"
        ).encode("utf-8")

        response = post_csv(content)

        assert response.status_code == 400
        assert "field larger than field limit" in response.json()["detail"]
    finally:
        csv.field_size_limit(original_limit)


def test_invalid_record_returns_200_with_validation_issue():
    content = (
        HEADER
        + "REQ-001,Иван,+79990000001,ivan@test.ru,7707083893,LOAN,125000.50,2026-09-12T10:30:00\n"
        + "REQ-002,Мария,+79990000002,maria@test.ru,7707083893,LOAN,0.00,2026-09-13T19:10:00\n"
    ).encode("utf-8")

    response = post_csv(content)

    assert response.status_code == 200
    body = response.json()
    assert len(body["valid_records"]) == 1
    assert body["valid_records"][0]["external_request_id"] == "REQ-001"
    assert len(body["issues"]) == 1
    assert body["issues"][0]["field"] == "amount"
    assert body["issues"][0]["error_type"] == "greater_than"
    assert body["issues"][0]["record_number"] == 3
    assert body["duplicate_request_ids"] == []
