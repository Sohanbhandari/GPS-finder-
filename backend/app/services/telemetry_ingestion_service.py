import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.gps_point import GpsPoint
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.mqtt import GpsTelemetryPayload


class TelemetryIngestionService:
    """
    Core telemetry processing service handling MQTT packet validation, atomic persistence,
    and out-of-order stale packet protection.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.vehicle_repo = VehicleRepository(session)

    async def process_payload(
        self,
        vehicle_code: str,
        raw_payload: Union[bytes, str, Dict[str, Any]],
    ) -> bool:
        """
        Ingests, validates, and persists a telemetry packet for a vehicle.

        Returns:
            bool: True if telemetry was successfully processed and committed, False if rejected.
        """
        received_at = datetime.now(timezone.utc)

        # 1. Parse JSON Payload
        if isinstance(raw_payload, (bytes, bytearray)):
            try:
                payload_dict = json.loads(raw_payload.decode("utf-8"))
            except Exception as err:
                logger.warning(f"Telemetry rejected for '{vehicle_code}': Malformed JSON payload ({err})")
                return False
        elif isinstance(raw_payload, str):
            try:
                payload_dict = json.loads(raw_payload)
            except Exception as err:
                logger.warning(f"Telemetry rejected for '{vehicle_code}': Malformed JSON string ({err})")
                return False
        elif isinstance(raw_payload, dict):
            payload_dict = raw_payload
        else:
            logger.warning(f"Telemetry rejected for '{vehicle_code}': Unsupported payload format")
            return False

        # 2. Pydantic Bounds & Type Validation
        try:
            telemetry = GpsTelemetryPayload.model_validate(payload_dict)
        except ValidationError as err:
            logger.warning(f"Telemetry rejected for '{vehicle_code}': Structural bounds validation failed ({err})")
            return False

        # 3. Known Vehicle Verification
        vehicle = await self.vehicle_repo.get_by_code(vehicle_code)
        if not vehicle:
            logger.warning(f"Telemetry rejected: Vehicle code '{vehicle_code}' not found in database.")
            return False

        recorded_at = telemetry.timestamp

        # 4. Atomic Transaction: Append to GpsPoint history
        gps_point = GpsPoint(
            vehicle_id=vehicle.id,
            latitude=telemetry.latitude,
            longitude=telemetry.longitude,
            speed=telemetry.speed,
            recorded_at=recorded_at,
            received_at=received_at,
        )
        self.session.add(gps_point)

        # 5. Out-of-Order Engine (Stale Packet Protection)
        # Normalize vehicle.latest_recorded_at timezone to UTC if naive
        latest_recorded = vehicle.latest_recorded_at
        if latest_recorded is not None and latest_recorded.tzinfo is None:
            latest_recorded = latest_recorded.replace(tzinfo=timezone.utc)

        is_newer_or_equal = (
            latest_recorded is None or recorded_at >= latest_recorded
        )

        if is_newer_or_equal:
            self.vehicle_repo.update_location_state(
                vehicle=vehicle,
                latitude=telemetry.latitude,
                longitude=telemetry.longitude,
                speed=telemetry.speed,
                recorded_at=recorded_at,
                received_at=received_at,
            )
            logger.info(
                f"Accepted telemetry for vehicle '{vehicle_code}': updated location state "
                f"(lat={telemetry.latitude}, lon={telemetry.longitude}, recorded_at={recorded_at.isoformat()})"
            )
        else:
            logger.info(
                f"Out-of-order telemetry for vehicle '{vehicle_code}': appended to history, "
                f"location state preserved (recorded_at={recorded_at.isoformat()} < "
                f"latest_recorded_at={vehicle.latest_recorded_at.isoformat()})"
            )

        await self.session.commit()
        return True
