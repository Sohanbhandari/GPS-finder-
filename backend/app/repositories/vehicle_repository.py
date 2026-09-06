from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle


class VehicleRepository:
    """
    Data access repository for Vehicle entity queries.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, vehicle_id: UUID) -> Optional[Vehicle]:
        """
        Retrieves a vehicle by primary key UUID.
        """
        stmt = select(Vehicle).where(Vehicle.id == vehicle_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, vehicle_code: str) -> Optional[Vehicle]:
        """
        Retrieves a vehicle by unique vehicle_code.
        """
        stmt = select(Vehicle).where(Vehicle.vehicle_code == vehicle_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def update_location_state(
        self,
        vehicle: Vehicle,
        latitude: float,
        longitude: float,
        speed: float,
        recorded_at: datetime,
        received_at: datetime,
    ) -> None:
        """
        Updates the denormalized location state and timestamps on a vehicle entity.
        """
        vehicle.current_latitude = latitude
        vehicle.current_longitude = longitude
        vehicle.current_speed = speed
        vehicle.latest_recorded_at = recorded_at
        vehicle.last_seen_at = received_at
