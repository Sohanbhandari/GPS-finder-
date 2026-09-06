from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_active_assignment,
    get_current_user,
    verify_vehicle_access,
)
from app.db.session import get_db
from app.models.assignment import Assignment
from app.schemas.assignment import AssignmentResponse
from app.schemas.telemetry import VehicleHistoryResponse
from app.schemas.vehicle import VehicleDetailResponse, VehicleLocationResponse
from app.services.telemetry_service import TelemetryService
from app.services.vehicle_service import VehicleService

router = APIRouter(tags=["User Active State"])


@router.get("/me/assignment", response_model=AssignmentResponse)
async def get_my_assignment(
    assignment: Assignment = Depends(get_active_assignment),
) -> AssignmentResponse:
    """
    Resolves the authenticated user's current active route and vehicle assignment.
    RouteStops are strictly ordered by sequence ASC for map polyline rendering.
    """
    return assignment


@router.get("/me/vehicle", response_model=VehicleDetailResponse)
async def get_my_vehicle(
    assignment: Assignment = Depends(get_active_assignment),
    db: AsyncSession = Depends(get_db),
) -> VehicleDetailResponse:
    """
    Retrieves metadata and computed status (ACTIVE, OFFLINE, UNKNOWN) for the user's assigned vehicle.
    """
    vehicle_service = VehicleService(db)
    return await vehicle_service.get_vehicle_detail(assignment.vehicle_id)


@router.get("/me/vehicle/location", response_model=VehicleLocationResponse)
async def get_my_vehicle_location(
    assignment: Assignment = Depends(get_active_assignment),
    db: AsyncSession = Depends(get_db),
) -> VehicleLocationResponse:
    """
    Retrieves current GPS coordinates, speed, recorded_at, and last_seen_at for user's assigned vehicle.
    """
    vehicle_service = VehicleService(db)
    return await vehicle_service.get_vehicle_location(assignment.vehicle_id)


@router.get("/me/vehicle/history", response_model=VehicleHistoryResponse)
async def get_my_vehicle_history(
    from_time: Optional[datetime] = Query(None, alias="from", description="ISO 8601 start timestamp filter"),
    to_time: Optional[datetime] = Query(None, alias="to", description="ISO 8601 end timestamp filter"),
    limit: int = Query(50, ge=1, le=200, description="Page item limit (clamped to max 200)"),
    cursor: Optional[UUID] = Query(None, description="Keyset pagination cursor UUID"),
    assignment: Assignment = Depends(get_active_assignment),
    db: AsyncSession = Depends(get_db),
) -> VehicleHistoryResponse:
    """
    Retrieves paginated historical telemetry points for user's assigned vehicle ordered by recorded_at DESC, id DESC.
    """
    telemetry_service = TelemetryService(db)
    return await telemetry_service.get_history_for_vehicle(
        vehicle_id=assignment.vehicle_id,
        from_time=from_time,
        to_time=to_time,
        limit=limit,
        cursor=cursor,
    )


@router.get("/vehicles/{vehicle_id}", response_model=VehicleDetailResponse)
async def get_vehicle_by_id(
    vehicle_id: UUID,
    assignment: Assignment = Depends(verify_vehicle_access),
    db: AsyncSession = Depends(get_db),
) -> VehicleDetailResponse:
    """
    Explicit vehicle endpoint enforcing server-side authorization.
    Returns HTTP 403 VEHICLE_ACCESS_DENIED if vehicle_id does not belong to user's active assignment.
    """
    vehicle_service = VehicleService(db)
    return await vehicle_service.get_vehicle_detail(vehicle_id)
