from http import HTTPStatus
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from operations_automation_hub.database import get_db
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.request import RequestCreate, RequestResponse, RequestStatus

app = FastAPI(title="Operations Automation Hub", version="0.1.0")


@app.get("/")
def get_root():
    return {"message": "Operations Automation Hub API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/requests", status_code=HTTPStatus.CREATED, response_model=RequestResponse)
def request_create(
    request_data: RequestCreate,
    session: Session = Depends(get_db),
) -> RequestResponse:
    data = request_data.model_dump()
    request = RequestModel(request_id=uuid4(), status=RequestStatus.NEW, **data)
    try:
        RequestRepository(session).create(request=request)
        session.commit()
    except IntegrityError as error:
        session.rollback()
        original_error = error.orig
        diag = getattr(original_error, "diag", None)
        constraint = getattr(diag, "constraint_name", None)
        if (
            getattr(original_error, "sqlstate", None) == "23505"
            and constraint == "requests_external_request_id_key"
        ):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT.value,
                detail="Request with this external_request_id already exists",
            ) from original_error
        raise
    return RequestResponse.model_validate(request, from_attributes=True)


@app.get(
    "/requests/{request_id}",
    response_model=RequestResponse,
    responses={
        HTTPStatus.NOT_FOUND.value: {
            "description": "Request not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Request not found",
                    }
                }
            },
        }
    },
)
def request_get(request_id: UUID, session: Session = Depends(get_db)) -> RequestResponse:
    repository = RequestRepository(session)
    request = repository.get_by_id(request_id)
    if request is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND.value, detail="Request not found")
    return RequestResponse.model_validate(request, from_attributes=True)
