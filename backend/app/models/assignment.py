import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.route import Route
    from app.models.vehicle import Vehicle


class Assignment(Base):
    """
    Assignment entity model mapping drivers to active or historical routes and vehicles.

    PostgreSQL Partial Uniqueness Rule:
        A driver may have multiple historical assignment records (is_active = False),
        but MUST have at most one ACTIVE assignment (is_active = True).
        This rule is enforced via PostgreSQL Partial Unique Index:
            CREATE UNIQUE INDEX idx_unique_active_user ON assignments(user_id) WHERE is_active = TRUE;

    Attributes:
        id: Unique primary key UUID.
        user_id: Foreign key linking to user (driver).
        route_id: Foreign key linking to assigned route.
        vehicle_id: Foreign key linking to assigned vehicle.
        is_active: Boolean flag indicating if assignment is currently active.
        assigned_at: UTC timestamp when assignment was created.
        updated_at: UTC timestamp when assignment state last changed.
    """
    __tablename__ = "assignments"
    __table_args__ = (
        Index("idx_assignments_route_vehicle", "route_id", "vehicle_id"),
        Index(
            "idx_unique_active_user",
            "user_id",
            unique=True,
            postgresql_where=(mapped_column("is_active") == True),
            sqlite_where=(mapped_column("is_active") == True),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="assignments",
        lazy="selectin",
    )
    route: Mapped["Route"] = relationship(
        "Route",
        back_populates="assignments",
        lazy="selectin",
    )
    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        back_populates="assignments",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Assignment id={self.id} user_id={self.user_id} active={self.is_active}>"
