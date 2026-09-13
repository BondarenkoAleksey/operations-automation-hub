from uuid import UUID

from operations_automation_hub.schemas.request import RequestResponse


class InMemoryRequestStore:
    def __init__(self):
        self._requests: dict[UUID, RequestResponse] = {}

    def save(self, request: RequestResponse) -> None:
        self._requests[request.request_id] = request

    def get(self, request_id: UUID) -> RequestResponse | None:
        return self._requests.get(request_id)
