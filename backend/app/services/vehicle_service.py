from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundException
from app.models.vehicle import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle import (
    VehicleDetailResponse,
    VehicleLocationResponse,
    VehicleStatusEnum,
)


class VehicleService:
    """
    Business service for calculating dynamic vehicle state and metadata.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.vehicle_repo = VehicleRepository(session)

    @staticmethod
    def compute_vehicle_status(
        last_seen_at: Optional[datetime],
        threshold_seconds: int = settings.ONLINE_THRESHOLD_SECONDS,
    ) -> VehicleStatusEnum:
        """
        Calculates authoritative vehicle status:
        - UNKNOWN: No telemetry recorded yet (last_seen_at is None)
        - ACTIVE: Telemetry received within threshold_seconds
        - OFFLINE: Telemetry older than threshold_seconds
        """
        if last_seen_at is None:
            return VehicleStatusEnum.UNKNOWN

        now = datetime.now(timezone.utc)
        if last_seen_at.tzinfo is None:
            last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)

        elapsed_seconds = (now - last_seen_at).total_seconds()
        if elapsed_seconds <= threshold_seconds:
            return VehicleStatusEnum.ACTIVE
        return VehicleStatusEnum.OFFLINE

    async def get_vehicle_detail(self, vehicle_id: UUID) -> VehicleDetailResponse:
        """
        Retrieves vehicle details and computes current status.
        """
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise ResourceNotFoundException("Vehicle not found.")

        status_enum = self.compute_vehicle_status(vehicle.last_seen_at)

        return VehicleDetailResponse(
            id=vehicle.id,
            vehicle_code=vehicle.vehicle_code,
            route_id=vehicle.route_id,
            status=status_enum,
            current_latitude=vehicle.current_latitude,
            current_longitude=vehicle.current_longitude,
            current_speed=vehicle.current_speed,
            latest_recorded_at=vehicle.latest_recorded_at,
            last_seen_at=vehicle.last_seen_at,
            created_at=vehicle.created_at,
        )

    async def get_vehicle_location(self, vehicle_id: UUID) -> VehicleLocationResponse:
        """
        Retrieves vehicle's current location and computed status for map rendering.
        """
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise ResourceNotFoundException("Vehicle not found.")

        status_enum = self.compute_vehicle_status(vehicle.last_seen_at)

        return VehicleLocationResponse(
            vehicle_id=vehicle.id,
            vehicle_code=vehicle.vehicle_code,
            status=status_enum,
            latitude=vehicle.current_latitude,
            longitude=vehicle.current_longitude,
            speed=vehicle.current_speed,
            latest_recorded_at=vehicle.latest_recorded_at,
            last_seen_at=vehicle.last_seen_at,
        )
