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
from app.schemas.vehicle import (
    VehicleDetailResponse,
    VehicleLocationResponse,
    VehicleStatusEnum,
)
from app.schemas.health import HealthResponse
from app.schemas.error import ErrorDetail, ErrorResponse
from app.schemas.telemetry import GpsPointResponse, VehicleHistoryResponse
from app.schemas.mqtt import GpsTelemetryPayload

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "AssignmentResponse",
    "RouteResponse",
    "RouteStopResponse",
    "VehicleSummaryResponse",
    "VehicleDetailResponse",
    "VehicleLocationResponse",
    "VehicleStatusEnum",
    "HealthResponse",
    "ErrorDetail",
    "ErrorResponse",
    "GpsPointResponse",
    "VehicleHistoryResponse",
    "GpsTelemetryPayload",
]
