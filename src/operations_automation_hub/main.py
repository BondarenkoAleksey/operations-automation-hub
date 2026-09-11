from fastapi import FastAPI

app = FastAPI(title="Operations Automation Hub", version="0.1.0")


@app.get("/")
def get_root():
    return {"message": "Operations Automation Hub API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
