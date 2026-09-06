from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check() -> HealthResponse:
    """
    Public system health check endpoint returning service status, version, and server timestamp.
    """
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
    )
