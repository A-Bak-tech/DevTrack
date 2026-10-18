
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth import router as auth_router
from app.security.rate_limit import limiter


app = FastAPI(
    title="DevTrack API",
    version="0.1.0",
)

# Register the rate limiter and its HTTP 429 handler.
app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
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
