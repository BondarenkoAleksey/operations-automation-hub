from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from operations_automation_hub.models.base import Base
from operations_automation_hub.schemas.job import JobStatus


class JobModel(Base):
    __tablename__ = "jobs"
    job_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
