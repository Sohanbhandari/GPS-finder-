import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.vehicle import Vehicle


class GpsPoint(Base):
    """
    GpsPoint entity model representing an immutable historical telemetry coordinate log.

    Attributes:
        id: Unique primary key UUID.
        vehicle_id: Foreign key linking telemetry reading to vehicle.
        latitude: Measured WGS84 latitude coordinate.
        longitude: Measured WGS84 longitude coordinate.
        speed: Measured speed in km/h or m/s.
        recorded_at: Source hardware timestamp when coordinate was sampled on vehicle.
        received_at: Server UTC timestamp when telemetry packet was ingested by backend.
    """
    __tablename__ = "gps_points"
    __table_args__ = (
        Index("idx_gps_points_vehicle_time", "vehicle_id", "recorded_at", "id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(
        Float(precision=53),
        nullable=False,
    )
    longitude: Mapped[float] = mapped_column(
        Float(precision=53),
        nullable=False,
    )
    speed: Mapped[float] = mapped_column(
        Float(precision=53),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        back_populates="gps_points",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<GpsPoint id={self.id} vehicle_id={self.vehicle_id} "
            f"lat={self.latitude} lon={self.longitude} recorded_at={self.recorded_at}>"
        )
