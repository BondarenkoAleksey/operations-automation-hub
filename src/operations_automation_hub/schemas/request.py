from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RequestStatus(StrEnum):
    NEW = "NEW"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    FAILED = "FAILED"


class RequestCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "external_request_id": "REQ-10001",
                "client_name": "Иван Петров",
                "phone": "+79991234567",
                "email": "ivan.petrov@example.test",
                "inn": "7707083893",
                "product_type": "CONSUMER_LOAN",
                "amount": "125000.5",
                "created_at": "2026-09-12T10:30:00",
            }
        },
    )
    external_request_id: str = Field(..., min_length=1, max_length=64)
    client_name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=32)
    email: str = Field(..., min_length=1, max_length=254)
    inn: str = Field(pattern=r"^\d{10}(\d{2})?$")
    product_type: str = Field(..., min_length=1, max_length=64)
    amount: Decimal = Field(..., gt=0)
    created_at: datetime


class RequestResponse(RequestCreate):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "external_request_id": "REQ-10001",
                "client_name": "Иван Петров",
                "phone": "+79991234567",
                "email": "ivan.petrov@example.test",
                "inn": "7707083893",
                "product_type": "CONSUMER_LOAN",
                "amount": "125000.5",
                "created_at": "2026-09-12T10:30:00",
                "status": "NEW",
            }
        },
    )
    request_id: UUID
    status: RequestStatus
