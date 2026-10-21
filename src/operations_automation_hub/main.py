import csv
from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from operations_automation_hub.database import get_db
from operations_automation_hub.importers.csv_import import validate_csv_file
from operations_automation_hub.models.request import RequestModel
from operations_automation_hub.repositories.job_repository import JobRepository
from operations_automation_hub.repositories.request_repository import RequestRepository
from operations_automation_hub.schemas.csv_import import CsvImportResponse, CsvValidationResult
from operations_automation_hub.schemas.job import JobResponse
from operations_automation_hub.schemas.request import RequestCreate, RequestResponse, RequestStatus
from operations_automation_hub.services.request_import_service import RequestImportService

MAX_CSV_SIZE = 1_048_576

app = FastAPI(title="Operations Automation Hub", version="0.1.0")


def _validate_uploaded_csv(file: UploadFile) -> CsvValidationResult:
    data = file.file.read(MAX_CSV_SIZE + 1)
    if len(data) > MAX_CSV_SIZE:
        raise HTTPException(413, "CSV file is too large")

    with TemporaryDirectory() as directory:
        csv_path = Path(directory) / "input.csv"
        csv_path.write_bytes(data)
        try:
            return validate_csv_file(csv_path)
        except UnicodeDecodeError as error:
            raise HTTPException(400, "CSV must be UTF-8 encoded") from error
        except (ValueError, csv.Error) as error:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=str(error),
            ) from error


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


@app.post(
    "/imports/csv/validate",
    response_model=CsvValidationResult,
)
def validate_csv_import(file: UploadFile) -> CsvValidationResult:
    return _validate_uploaded_csv(file)


@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    responses={
        HTTPStatus.NOT_FOUND.value: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Job not found",
                    }
                }
            },
        }
    },
)
def job_get(job_id: UUID, session: Session = Depends(get_db)) -> JobResponse:
    repository = JobRepository(session)
    job = repository.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND.value, detail="Job not found")
    return JobResponse.model_validate(job)


@app.post(
    "/imports/csv",
    status_code=HTTPStatus.OK,
    response_model=CsvImportResponse,
)
def import_csv_requests(
    file: UploadFile,
    session: Session = Depends(get_db),
) -> CsvImportResponse:
    validation_result = _validate_uploaded_csv(file)
    try:
        service = RequestImportService(session)
        result = service.import_requests(validation_result.valid_records)

        job_response = JobResponse.model_validate(result.job) if result.job is not None else None

        response = CsvImportResponse(
            job=job_response,
            imported_count=result.imported_count,
            issues=validation_result.issues,
            duplicate_request_ids=result.duplicate_request_ids,
            existing_request_ids=result.existing_request_ids,
        )

        session.commit()
    except Exception:
        session.rollback()
        raise
    return response
