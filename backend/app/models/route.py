import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.route_stop import RouteStop
    from app.models.vehicle import Vehicle
    from app.models.assignment import Assignment


class Route(Base):
    """
    Route entity model defining a transit path with sequential stops.

    Attributes:
        id: Unique primary key UUID.
        code: Unique human-readable route identifier code (e.g., 'ROUTE-A').
        name: Full descriptive route title (e.g., 'Main Campus Loop').
        description: Extended description of the route.
        created_at: Time stamp when the route was registered in UTC.
    """
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    stops: Mapped[List["RouteStop"]] = relationship(
        "RouteStop",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="RouteStop.sequence",
        lazy="selectin",
    )
    vehicles: Mapped[List["Vehicle"]] = relationship(
        "Vehicle",
        back_populates="route",
        lazy="selectin",
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="route",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Route id={self.id} code={self.code} name={self.name}>"
