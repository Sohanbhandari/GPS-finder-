from datetime import datetime, timezone
from typing import Any, Union
from pydantic import BaseModel, Field, field_validator


class GpsTelemetryPayload(BaseModel):
    """
    Pydantic schema for validating inbound MQTT vehicle telemetry payloads.
    Enforces WGS84 coordinate bounds, non-negative speed, and UTC timestamp parsing.
    """
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude (-180 to +180)")
    speed: float = Field(..., ge=0.0, description="Vehicle speed in km/h or m/s (>= 0)")
    timestamp: Union[datetime, float, int, str] = Field(
        ...,
        description="Source measurement timestamp (ISO 8601 string or numeric Epoch timestamp)",
    )

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_recorded_at(cls, value: Any) -> datetime:
        """
        Parses various timestamp representations (ISO 8601 string, float, int, datetime)
        and converts to a timezone-aware UTC datetime object.
        """
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)

        if isinstance(value, str):
            value_str = value.strip()
            # Try numeric string
            try:
                numeric_val = float(value_str)
                return datetime.fromtimestamp(numeric_val, tz=timezone.utc)
            except ValueError:
                pass

            # Try ISO 8601 string parsing
            try:
                dt = datetime.fromisoformat(value_str.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError as err:
                raise ValueError(f"Invalid ISO 8601 or numeric timestamp: {value_str}") from err

        raise ValueError(f"Unsupported timestamp format: {type(value)}")
