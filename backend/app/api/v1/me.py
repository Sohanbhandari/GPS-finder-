from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_active_assignment,
    get_current_user,
    verify_vehicle_access,
)
from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.user import User
from app.schemas.assignment import AssignmentResponse
from app.schemas.vehicle import VehicleDetailResponse
from app.services.vehicle_service import VehicleService

router = APIRouter(tags=["User Active State"])


@router.get("/me/assignment", response_model=AssignmentResponse)
async def get_my_assignment(
    assignment: Assignment = Depends(get_active_assignment),
) -> AssignmentResponse:
    """
    Resolves the authenticated user's current active route and vehicle assignment.
    """
    return assignment


@router.get("/me/vehicle", response_model=VehicleDetailResponse)
async def get_my_vehicle(
    assignment: Assignment = Depends(get_active_assignment),
    db: AsyncSession = Depends(get_db),
) -> VehicleDetailResponse:
    """
    Retrieves metadata and computed status for the current user's assigned vehicle.
    """
    vehicle_service = VehicleService(db)
    return await vehicle_service.get_vehicle_detail(assignment.vehicle_id)


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
