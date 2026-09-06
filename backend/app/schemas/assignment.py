from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RouteStopResponse(BaseModel):
    """
    Geographical waypoint stop along a route.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence: int
    name: str
    latitude: float
    longitude: float


class RouteResponse(BaseModel):
    """
    Route metadata and list of ordered stops.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    stops: List[RouteStopResponse] = []


class VehicleSummaryResponse(BaseModel):
    """
    Summary vehicle attributes mapped within an assignment response.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_code: str
    route_id: UUID
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_speed: Optional[float] = None
    latest_recorded_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    """
    Detailed active assignment mapping a user to a route and vehicle.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    is_active: bool
    assigned_at: datetime
    updated_at: datetime
    route: RouteResponse
    vehicle: VehicleSummaryResponse
