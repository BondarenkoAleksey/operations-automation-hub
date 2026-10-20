from dataclasses import dataclass, field

from operations_automation_hub.models.job import JobModel


@dataclass
class RequestImportResult:
    job: JobModel | None
    imported_count: int
    duplicate_request_ids: list[str] = field(default_factory=list)
    existing_request_ids: list[str] = field(default_factory=list)
