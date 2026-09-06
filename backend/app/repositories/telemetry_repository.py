from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gps_point import GpsPoint


class TelemetryRepository:
    """
    Data access repository for GpsPoint historical telemetry queries.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_vehicle_history(
        self,
        vehicle_id: UUID,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        limit: int = 50,
        cursor: Optional[UUID] = None,
    ) -> Tuple[List[GpsPoint], bool]:
        """
        Retrieves paginated historical telemetry for a vehicle ordered deterministically by recorded_at DESC, id DESC.
        Returns tuple of (items, has_more).
        """
        stmt = select(GpsPoint).where(GpsPoint.vehicle_id == vehicle_id)

        if from_time:
            stmt = stmt.where(GpsPoint.recorded_at >= from_time)
        if to_time:
            stmt = stmt.where(GpsPoint.recorded_at <= to_time)

        # Keyset Pagination Cursor Handling
        if cursor:
            cursor_point_stmt = select(GpsPoint).where(GpsPoint.id == cursor)
            cursor_res = await self.session.execute(cursor_point_stmt)
            cursor_point = cursor_res.scalar_one_or_none()

            if cursor_point:
                # Deterministic composite keyset comparison: (recorded_at, id) < (cursor.recorded_at, cursor.id)
                stmt = stmt.where(
                    tuple_(GpsPoint.recorded_at, GpsPoint.id) < (cursor_point.recorded_at, cursor_point.id)
                )

        stmt = stmt.order_by(GpsPoint.recorded_at.desc(), GpsPoint.id.desc())

        # Fetch limit + 1 to determine has_more
        stmt = stmt.limit(limit + 1)
        result = await self.session.execute(stmt)
        points = list(result.scalars().all())

        has_more = len(points) > limit
        if has_more:
            points = points[:limit]

        return points, has_more
