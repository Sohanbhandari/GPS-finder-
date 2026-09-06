import asyncio
from datetime import datetime, timezone
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models import Assignment, GpsPoint, Route, RouteStop, User, Vehicle

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def seed_database(session: AsyncSession) -> None:
    """
    Populates the database with deterministic initial development seed data.
    Idempotently checks if seed data exists before insertion.
    """
    logger.info("Checking existing seed data...")

    # Check if User A exists
    user_a_stmt = select(User).where(User.email == "driver.a@example.com")
    existing_user_a = (await session.execute(user_a_stmt)).scalar_one_or_none()

    if existing_user_a:
        logger.info("Seed data already present in database. Skipping seed initialization.")
        return

    logger.info("Seeding database with initial users, routes, stops, vehicles, and active assignments...")

    default_password_hash = get_password_hash("Password123!")
    now = datetime.now(timezone.utc)

    # 1. Users
    user_a = User(
        email="driver.a@example.com",
        password_hash=default_password_hash,
        full_name="Driver Alice",
        role="driver",
        is_active=True,
    )
    user_b = User(
        email="driver.b@example.com",
        password_hash=default_password_hash,
        full_name="Driver Bob",
        role="driver",
        is_active=True,
    )
    session.add_all([user_a, user_b])
    await session.flush()

    # 2. Routes
    route_a = Route(
        code="ROUTE-A",
        name="North Campus Loop",
        description="Loop connecting Central Station, Library, Engineering Block, Science Hub, Student Center, and North Gate.",
    )
    route_b = Route(
        code="ROUTE-B",
        name="South City Express",
        description="Express route connecting South Station, Commercial Park, Tech Park, Civic Center, South Plaza, and Terminal B.",
    )
    session.add_all([route_a, route_b])
    await session.flush()

    # 3. Route Stops for Route A
    stops_a = [
        RouteStop(route_id=route_a.id, sequence=1, name="Central Station", latitude=27.700769, longitude=85.300140),
        RouteStop(route_id=route_a.id, sequence=2, name="Library Gate", latitude=27.702500, longitude=85.303100),
        RouteStop(route_id=route_a.id, sequence=3, name="Engineering Complex", latitude=27.705000, longitude=85.306000),
        RouteStop(route_id=route_a.id, sequence=4, name="Science Hub", latitude=27.708000, longitude=85.304000),
        RouteStop(route_id=route_a.id, sequence=5, name="Student Union", latitude=27.706000, longitude=85.301000),
        RouteStop(route_id=route_a.id, sequence=6, name="North Gate Terminal", latitude=27.703000, longitude=85.299000),
    ]

    # Route Stops for Route B
    stops_b = [
        RouteStop(route_id=route_b.id, sequence=1, name="South Station", latitude=27.680000, longitude=85.310000),
        RouteStop(route_id=route_b.id, sequence=2, name="Commercial Park", latitude=27.683000, longitude=85.314000),
        RouteStop(route_id=route_b.id, sequence=3, name="Tech Park Tower", latitude=27.687000, longitude=85.318000),
        RouteStop(route_id=route_b.id, sequence=4, name="Civic Center", latitude=27.691000, longitude=85.315000),
        RouteStop(route_id=route_b.id, sequence=5, name="South Plaza", latitude=27.688000, longitude=85.311000),
        RouteStop(route_id=route_b.id, sequence=6, name="Terminal B", latitude=27.684000, longitude=85.308000),
    ]
    session.add_all(stops_a + stops_b)
    await session.flush()

    # 4. Vehicles
    vehicle_a = Vehicle(
        vehicle_code="BUS-001",
        route_id=route_a.id,
        current_latitude=27.700769,
        current_longitude=85.300140,
        current_speed=0.0,
        latest_recorded_at=now,
        last_seen_at=now,
    )
    vehicle_b = Vehicle(
        vehicle_code="BUS-002",
        route_id=route_b.id,
        current_latitude=27.680000,
        current_longitude=85.310000,
        current_speed=0.0,
        latest_recorded_at=now,
        last_seen_at=now,
    )
    session.add_all([vehicle_a, vehicle_b])
    await session.flush()

    # 5. Assignments (User A -> Route A -> BUS-001, User B -> Route B -> BUS-002)
    assignment_a = Assignment(
        user_id=user_a.id,
        route_id=route_a.id,
        vehicle_id=vehicle_a.id,
        is_active=True,
    )
    assignment_b = Assignment(
        user_id=user_b.id,
        route_id=route_b.id,
        vehicle_id=vehicle_b.id,
        is_active=True,
    )
    session.add_all([assignment_a, assignment_b])
    await session.flush()

    # 6. Initial GPS Points
    gps_point_a = GpsPoint(
        vehicle_id=vehicle_a.id,
        latitude=27.700769,
        longitude=85.300140,
        speed=0.0,
        recorded_at=now,
        received_at=now,
    )
    gps_point_b = GpsPoint(
        vehicle_id=vehicle_b.id,
        latitude=27.680000,
        longitude=85.310000,
        speed=0.0,
        recorded_at=now,
        received_at=now,
    )
    session.add_all([gps_point_a, gps_point_b])

    await session.commit()
    logger.info("Successfully seeded database with deterministic development data.")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_database(session)


if __name__ == "__main__":
    asyncio.run(main())
