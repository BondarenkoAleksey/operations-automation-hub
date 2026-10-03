from operations_automation_hub.schemas.request import RequestCreate


def validate_csv_record(record: dict[str, str]) -> RequestCreate:
    return RequestCreate.model_validate(record)
