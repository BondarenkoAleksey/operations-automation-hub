from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from operations_automation_hub.models.base import Base
from operations_automation_hub.schemas.request import RequestStatus


class RequestModel(Base):
    __tablename__ = "requests"
    request_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, nullable=False)
    external_request_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), nullable=False)
    product_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status"), nullable=False
    )
