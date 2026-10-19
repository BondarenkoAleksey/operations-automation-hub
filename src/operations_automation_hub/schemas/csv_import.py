from pydantic import BaseModel, Field

from operations_automation_hub.schemas.job import JobResponse
from operations_automation_hub.schemas.request import RequestCreate


class CsvValidationIssue(BaseModel):
    record_number: int = Field(..., ge=2)
    field: str
    message: str
    error_type: str


class CsvValidationResult(BaseModel):
    valid_records: list[RequestCreate] = Field(default_factory=list)
    issues: list[CsvValidationIssue] = Field(default_factory=list)
    duplicate_request_ids: list[str] = Field(default_factory=list)


class CsvImportResponse(BaseModel):
    job: JobResponse | None
    imported_count: int = Field(..., ge=0)
    issues: list[CsvValidationIssue] = Field(default_factory=list)
    duplicate_request_ids: list[str] = Field(default_factory=list)
    existing_request_ids: list[str] = Field(default_factory=list)
