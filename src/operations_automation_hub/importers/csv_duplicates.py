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


def exclude_duplicate_requests(
    requests: list[RequestCreate],
) -> list[RequestCreate]:
    duplicates = find_duplicate_request_ids(requests)
    filtered = []
    for request in requests:
        if request.external_request_id not in duplicates:
            filtered.append(request)
    return filtered
