from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.telemetry import GpsPointResponse, VehicleHistoryResponse


class TelemetryService:
    """
    Business service handling vehicle historical telemetry reads and query validation.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.telemetry_repo = TelemetryRepository(session)

    async def get_history_for_vehicle(
        self,
        vehicle_id: UUID,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        limit: int = 50,
        cursor: Optional[UUID] = None,
    ) -> VehicleHistoryResponse:
        """
        Retrieves paginated historical telemetry points for a vehicle.
        Enforces date range validation (from_time <= to_time) and limit clamping (max 200).
        """
        if from_time and to_time and from_time > to_time:
            raise AppException(
                code="VALIDATION_ERROR",
                message="Query parameter 'from' cannot be greater than 'to'.",
                status_code=422,
            )

        # Server-side limit clamping to maximum 200
        clamped_limit = min(max(1, limit), 200)

        points, has_more = await self.telemetry_repo.get_vehicle_history(
            vehicle_id=vehicle_id,
            from_time=from_time,
            to_time=to_time,
            limit=clamped_limit,
            cursor=cursor,
        )

        item_responses = [GpsPointResponse.model_validate(p) for p in points]
        next_cursor = str(points[-1].id) if has_more and points else None

        return VehicleHistoryResponse(
            items=item_responses,
            next_cursor=next_cursor,
            has_more=has_more,
        )
