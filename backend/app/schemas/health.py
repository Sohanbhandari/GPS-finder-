from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    System health check status response model.
    """
    status: str = Field("ok", description="System operational status")
    version: str = Field(..., description="API system version string")
    timestamp: datetime = Field(..., description="Server current UTC timestamp")
