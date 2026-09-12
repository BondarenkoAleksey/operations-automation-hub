from http import HTTPStatus

from fastapi import FastAPI

from operations_automation_hub.schemas.request import RequestCreate

app = FastAPI(title="Operations Automation Hub", version="0.1.0")


@app.get("/")
def get_root():
    return {"message": "Operations Automation Hub API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/requests", status_code=HTTPStatus.CREATED, response_model=RequestCreate)
def request_create(request_model: RequestCreate) -> RequestCreate:
    return request_model
