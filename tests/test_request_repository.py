from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from operations_automation_hub.database import SessionLocal
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.request import RequestStatus


@pytest.mark.integration
def test_create_and_get_request():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            request_id = uuid4()
            request = RequestModel(
                request_id=request_id,
                external_request_id=f"TEST-{uuid4()}",
                client_name="Тест Тестович",
                phone="+79001234567",
                email="mail@mail.com",
                inn="841827179762",
                product_type="тест_тип_продукта",
                amount=Decimal("125000.50"),
                created_at=datetime(year=2026, month=9, day=1, tzinfo=timezone.utc),
                status=RequestStatus.NEW,
            )
            repository.create(request)
            session.expunge_all()
            found = repository.get_by_id(request_id)
            assert found is not request
            assert found is not None
            assert found.request_id == request_id
            assert found.external_request_id == request.external_request_id
            assert found.client_name == request.client_name
            assert found.phone == request.phone
            assert found.email == request.email
            assert found.inn == request.inn
            assert found.product_type == request.product_type
            assert found.amount == request.amount
            assert found.created_at == request.created_at
            assert found.status == RequestStatus.NEW
        finally:
            session.rollback()


@pytest.mark.integration
def test_get_by_id_returns_none_for_missing():
    with SessionLocal() as session:
        repository = RequestRepository(session)
        try:
            random_id = uuid4()
            result = repository.get_by_id(random_id)
            assert result is None
        finally:
            session.rollback()
