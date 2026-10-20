from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from operations_automation_hub.importers.csv_duplicates import exclude_duplicate_requests
from operations_automation_hub.models.job import JobModel
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.job import JobStatus
from operations_automation_hub.schemas.request import RequestCreate, RequestStatus
from operations_automation_hub.services.request_import_result import RequestImportResult


class RequestImportService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._job_repository = JobRepository(session)
        self._request_repository = RequestRepository(session)

    def import_requests(self, requests: list[RequestCreate]) -> RequestImportResult:
        counts = Counter(r.external_request_id for r in requests)
        duplicate_request_ids = sorted(
            request_id for request_id, count in counts.items() if count > 1
        )

        unique = exclude_duplicate_requests(requests)
        if not unique:
            return RequestImportResult(
                job=None,
                imported_count=0,
                duplicate_request_ids=duplicate_request_ids,
            )

        candidate_ids = {r.external_request_id for r in unique}
        existing_ids = self._request_repository.find_existing_external_request_ids(candidate_ids)
        existing_request_ids = sorted(existing_ids)
        fresh = [r for r in unique if r.external_request_id not in existing_ids]
        if not fresh:
            return RequestImportResult(
                job=None,
                imported_count=0,
                duplicate_request_ids=duplicate_request_ids,
                existing_request_ids=existing_request_ids,
            )

        job = JobModel(
            job_id=uuid4(),
            status=JobStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )
        self._job_repository.create(job)

        for request_create in fresh:
            data = request_create.model_dump()
            request_model = RequestModel(
                request_id=uuid4(),
                status=RequestStatus.NEW,
                job_id=job.job_id,
                **data,
            )
            self._request_repository.create(request_model)

        return RequestImportResult(
            job=job,
            imported_count=len(fresh),
            duplicate_request_ids=duplicate_request_ids,
            existing_request_ids=existing_request_ids,
        )
