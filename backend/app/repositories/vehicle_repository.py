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
