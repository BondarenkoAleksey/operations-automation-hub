from operations_automation_hub.schemas.request import RequestCreate


def find_duplicate_request_ids(
    requests: list[RequestCreate],
) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for request in requests:
        request_id = request.external_request_id
        if request_id in seen:
            duplicates.add(request_id)
        seen.add(request_id)
    return duplicates
