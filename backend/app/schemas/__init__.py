"""
Pydantic API Schemas Package.
"""
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.assignment import (
    AssignmentResponse,
    RouteResponse,
    RouteStopResponse,
    VehicleSummaryResponse,
)
from app.schemas.vehicle import VehicleDetailResponse, VehicleStatusEnum

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "AssignmentResponse",
    "RouteResponse",
    "RouteStopResponse",
    "VehicleSummaryResponse",
    "VehicleDetailResponse",
    "VehicleStatusEnum",
]
