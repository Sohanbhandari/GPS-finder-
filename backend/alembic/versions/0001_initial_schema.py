"""Initial database schema migration creating users, routes, route_stops, vehicles, assignments, and gps_points.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="driver"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)

    # 2. routes table
    op.create_table(
        "routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_routes_code", "routes", ["code"], unique=True)

    # 3. route_stops table
    op.create_table(
        "route_stops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(precision=53), nullable=False),
        sa.Column("longitude", sa.Float(precision=53), nullable=False),
        sa.UniqueConstraint("route_id", "sequence", name="uq_route_stop_sequence"),
    )
    op.create_index("idx_route_stops_seq", "route_stops", ["route_id", "sequence"])

    # 4. vehicles table
    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_code", sa.String(length=50), nullable=False),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("current_latitude", sa.Float(precision=53), nullable=True),
        sa.Column("current_longitude", sa.Float(precision=53), nullable=True),
        sa.Column("current_speed", sa.Float(precision=53), nullable=True),
        sa.Column("latest_recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_vehicles_code", "vehicles", ["vehicle_code"], unique=True)
    op.create_index("idx_vehicles_route", "vehicles", ["route_id"])

    # 5. assignments table
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_assignments_route_vehicle", "assignments", ["route_id", "vehicle_id"])
    
    # Partial unique index enforcing single active assignment per user
    op.create_index(
        "idx_unique_active_user",
        "assignments",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),
        sqlite_where=sa.text("is_active = TRUE"),
    )

    # 6. gps_points table
    op.create_table(
        "gps_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("latitude", sa.Float(precision=53), nullable=False),
        sa.Column("longitude", sa.Float(precision=53), nullable=False),
        sa.Column("speed", sa.Float(precision=53), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_gps_points_vehicle_time", "gps_points", ["vehicle_id", "recorded_at", "id"])


def downgrade() -> None:
    op.drop_index("idx_gps_points_vehicle_time", table_name="gps_points")
    op.drop_table("gps_points")

    op.drop_index("idx_unique_active_user", table_name="assignments")
    op.drop_index("idx_assignments_route_vehicle", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("idx_vehicles_route", table_name="vehicles")
    op.drop_index("idx_vehicles_code", table_name="vehicles")
    op.drop_table("vehicles")

    op.drop_index("idx_route_stops_seq", table_name="route_stops")
    op.drop_table("route_stops")

    op.drop_index("idx_routes_code", table_name="routes")
    op.drop_table("routes")

    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
