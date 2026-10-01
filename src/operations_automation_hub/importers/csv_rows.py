from operations_automation_hub.importers.csv_header import validate_csv_header


def csv_row_to_dict(header: list[str], row: list[str]) -> dict[str, str]:
    validate_csv_header(header)
    return dict(zip(header, row, strict=True))
