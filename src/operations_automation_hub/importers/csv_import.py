from pathlib import Path

from operations_automation_hub.importers.csv_duplicates import find_duplicate_request_ids
from operations_automation_hub.importers.csv_rows import read_csv_records
from operations_automation_hub.importers.csv_validation import validate_csv_records
from operations_automation_hub.schemas.csv_import import CsvValidationResult


def validate_csv_file(path: Path) -> CsvValidationResult:
    records = read_csv_records(path)
    result = validate_csv_records(records)
    duplicate_request_ids = find_duplicate_request_ids(result.valid_records)
    sorted_duplicate_request_ids = sorted(duplicate_request_ids)
    result.duplicate_request_ids = sorted_duplicate_request_ids
    return result
