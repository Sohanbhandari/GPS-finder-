import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.route import Route
    from app.models.assignment import Assignment
    from app.models.gps_point import GpsPoint


class Vehicle(Base):
    """
    Vehicle entity model representing physical tracked transit vehicles.

    Attributes:
        id: Unique primary key UUID.
        vehicle_code: Unique vehicle identifier code (e.g., 'BUS-001').
        route_id: Foreign key linking vehicle to assigned route.
        current_latitude: Cached current latitude coordinate from latest telemetry.
        current_longitude: Cached current longitude coordinate from latest telemetry.
        current_speed: Cached current speed in km/h or m/s from latest telemetry.
        latest_recorded_at: Source hardware timestamp of latest applied telemetry (out-of-order guard).
        last_seen_at: Server receipt timestamp of latest applied telemetry.
        created_at: Time stamp when vehicle was registered in UTC.
    """
    __tablename__ = "vehicles"
    __table_args__ = (
        Index("idx_vehicles_route", "route_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    vehicle_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    current_latitude: Mapped[Optional[float]] = mapped_column(
        Float(precision=53),
        nullable=True,
    )
    current_longitude: Mapped[Optional[float]] = mapped_column(
        Float(precision=53),
        nullable=True,
    )
    current_speed: Mapped[Optional[float]] = mapped_column(
        Float(precision=53),
        nullable=True,
    )
    latest_recorded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    route: Mapped["Route"] = relationship(
        "Route",
        back_populates="vehicles",
        lazy="selectin",
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="vehicle",
        lazy="selectin",
    )
    gps_points: Mapped[List["GpsPoint"]] = relationship(
        "GpsPoint",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} code={self.vehicle_code} route_id={self.route_id}>"
