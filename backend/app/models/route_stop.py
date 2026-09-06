import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.route import Route


class RouteStop(Base):
    """
    RouteStop entity model representing ordered geographical waypoints along a route.

    Attributes:
        id: Unique primary key UUID.
        route_id: Foreign key linking stop to parent route.
        sequence: Zero- or one-based sequence index defining stop order.
        name: Human readable stop title.
        latitude: WGS84 latitude coordinate.
        longitude: WGS84 longitude coordinate.
    """
    __tablename__ = "route_stops"
    __table_args__ = (
        Index("idx_route_stops_seq", "route_id", "sequence"),
        UniqueConstraint("route_id", "sequence", name="uq_route_stop_sequence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
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

    # Relationships
    route: Mapped["Route"] = relationship(
        "Route",
        back_populates="stops",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<RouteStop id={self.id} route_id={self.route_id} seq={self.sequence} name={self.name}>"
