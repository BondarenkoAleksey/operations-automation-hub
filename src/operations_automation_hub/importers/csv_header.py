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
