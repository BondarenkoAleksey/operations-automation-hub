import csv
from pathlib import Path

from operations_automation_hub.importers.csv_header import validate_csv_header


def csv_row_to_dict(header: list[str], row: list[str]) -> dict[str, str]:
    validate_csv_header(header)
    return dict(zip(header, row, strict=True))


def read_csv_records(path: Path) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, None)
        if header is None:
            raise ValueError("Пустой заголовок")
        validate_csv_header(header=header)
        len_header = len(header)
        records = []
        for record_number, row in enumerate(reader, start=2):
            if len(row) != len_header:
                raise ValueError(
                    f"Запись {record_number}: ожидалось {len_header} полей, получено {len(row)}."
                )
            records.append(csv_row_to_dict(header=header, row=row))
        return records
