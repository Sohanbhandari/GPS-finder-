from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class VehicleStatusEnum(str, Enum):
    """
    Computed online status of a tracked vehicle.
    """
    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"


class VehicleDetailResponse(BaseModel):
    """
    Full vehicle metadata and computed status response.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_code: str
    route_id: UUID
    status: VehicleStatusEnum = Field(..., description="Computed status: ACTIVE, OFFLINE, or UNKNOWN")
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_speed: Optional[float] = None
    latest_recorded_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
