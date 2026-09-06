from fastapi import APIRouter

router = APIRouter()


@router.get("/health", status_code=200)
async def health_check():
    """
    Public system health check endpoint.
    """
    return {
        "status": "ok",
        "service": "gps-tracker-api"
    }
