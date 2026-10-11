from uuid import UUID

from sqlalchemy.orm import Session

from operations_automation_hub.models.job import JobModel


class JobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, job: JobModel) -> JobModel:
        self._session.add(job)
        self._session.flush()
        return job

    def get_by_id(self, job_id: UUID) -> JobModel | None:
        return self._session.get(JobModel, job_id)
