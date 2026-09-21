from uuid import UUID

from sqlalchemy.orm import Session

from operations_automation_hub.models.request import RequestModel


class RequestRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, request: RequestModel) -> RequestModel:
        self._session.add(request)
        self._session.flush()
        return request

    def get_by_id(self, request_id: UUID) -> RequestModel | None:
        return self._session.get(RequestModel, request_id)
