from pydantic import ValidationError

from operations_automation_hub.schemas.csv_import import CsvValidationIssue, CsvValidationResult
from operations_automation_hub.schemas.request import RequestCreate


def validate_csv_record(record: dict[str, str]) -> RequestCreate:
    return RequestCreate.model_validate(record)


def validate_csv_records(
    records: list[dict[str, str]],
) -> CsvValidationResult:
    result = CsvValidationResult()
    for number, record in enumerate(records, start=2):
        try:
            valid = validate_csv_record(record)
        except ValidationError as exc:
            for error in exc.errors():
                result.issues.append(
                    CsvValidationIssue(
                        record_number=number,
                        field=error["loc"][0],
                        message=error["msg"],
                        error_type=error["type"],
                    )
                )
            continue
        result.valid_records.append(valid)
    return result
