from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class GpsPointResponse(BaseModel):
    """
    Historical GPS telemetry coordinate log.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_id: UUID
    latitude: float
    longitude: float
    speed: float
    recorded_at: datetime = Field(..., description="Source hardware measurement timestamp")
    received_at: datetime = Field(..., description="Server ingestion timestamp")


class VehicleHistoryResponse(BaseModel):
    """
    Paginated historical telemetry response envelope.
    """
    items: List[GpsPointResponse] = Field(..., description="List of historical GPS telemetry points")
    next_cursor: Optional[str] = Field(None, description="Keyset pagination cursor for retrieving next page")
    has_more: bool = Field(False, description="Flag indicating if additional records exist beyond current page")
