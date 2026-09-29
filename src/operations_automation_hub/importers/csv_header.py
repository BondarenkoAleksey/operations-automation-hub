import csv
from pathlib import Path


def validate_csv_header(header: list[str]) -> None:
    expected = {
        "external_request_id",
        "client_name",
        "phone",
        "email",
        "inn",
        "product_type",
        "amount",
        "created_at",
    }
    if not header:
        raise ValueError("Пустой заголовок")
    duplicates = [col for col in header if header.count(col) > 1]
    if duplicates:
        raise ValueError(f"Дублирующиеся столбцы {duplicates}")
    if expected - set(header):
        raise ValueError(f"Не хватает столбцов - {expected - set(header)}")
    if set(header) - expected:
        raise ValueError(f"Лишние столбцы - {set(header) - expected}")


def read_csv_header(path: Path) -> list[str]:
    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, None)
        if header is None:
            raise ValueError("Пустой заголовок")
        validate_csv_header(header=header)
        return header


def read_csv_rows(path: Path) -> list[list[str]]:
    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, None)
        if header is None:
            raise ValueError("Пустой заголовок")
        validate_csv_header(header=header)
        return list(reader)
