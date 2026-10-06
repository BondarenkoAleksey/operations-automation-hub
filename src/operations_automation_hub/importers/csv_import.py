from pathlib import Path

from operations_automation_hub.importers.csv_rows import read_csv_records
from operations_automation_hub.importers.csv_validation import validate_csv_records
from operations_automation_hub.schemas.csv_import import CsvValidationResult


def validate_csv_file(path: Path) -> CsvValidationResult:
    records = read_csv_records(path)
    return validate_csv_records(records)
