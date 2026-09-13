from http import HTTPStatus
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException

from operations_automation_hub.schemas.request import RequestCreate, RequestResponse, RequestStatus
from operations_automation_hub.storage.request_store import InMemoryRequestStore

app = FastAPI(title="Operations Automation Hub", version="0.1.0")
request_store = InMemoryRequestStore()


@app.get("/")
def get_root():
    return {"message": "Operations Automation Hub API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/requests", status_code=HTTPStatus.CREATED, response_model=RequestResponse)
def request_create(request_model: RequestCreate) -> RequestResponse:
    data = request_model.model_dump()
    request_id = uuid4()
    request_response = RequestResponse(request_id=request_id, status=RequestStatus.NEW, **data)
    request_store.save(request_response)
    return request_response


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
def request_get(request_id: UUID) -> RequestResponse:
    request = request_store.get(request_id)
    if request is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Request not found")
    return request
