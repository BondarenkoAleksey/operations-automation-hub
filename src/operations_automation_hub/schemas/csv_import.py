from pydantic import BaseModel, Field

from operations_automation_hub.schemas.request import RequestCreate


class CsvValidationIssue(BaseModel):
    record_number: int = Field(..., ge=2)
    field: str
    message: str
    error_type: str


class CsvValidationResult(BaseModel):
    valid_records: list[RequestCreate] = Field(default_factory=list)
    issues: list[CsvValidationIssue] = Field(default_factory=list)
