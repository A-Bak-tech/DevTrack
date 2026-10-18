
from fastapi import FastAPI

from app.api.v1.auth import router as auth_router

app = FastAPI(
    title="DevTrack API",
    version="0.1.0",
)

app.include_router(
    auth_router,
    prefix="/api/v1",
)


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "devtrack-api",
    }
