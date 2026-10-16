from uuid import UUID

from sqlalchemy import select
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

    def find_existing_external_request_ids(
        self,
        external_request_ids: set[str],
    ) -> set[str]:
        if not external_request_ids:
            return set()
        stmt = select(RequestModel.external_request_id).where(
            RequestModel.external_request_id.in_(external_request_ids)
        )
        return set(self._session.scalars(stmt))
