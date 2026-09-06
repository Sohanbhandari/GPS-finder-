import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.models import User, Route, RouteStop, Vehicle, Assignment, GpsPoint
from app.db.seed import seed_database


@pytest_asyncio.fixture
async def test_engine():
    # SQLite in-memory with async driver for fast isolated tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_models_creation_and_query(test_session: AsyncSession):
    """
    Verify ORM models can be inserted and queried properly.
    """
    user = User(
        email="testdriver@example.com",
        password_hash="hashed_pw",
        full_name="Test Driver",
        role="driver",
    )
    test_session.add(user)
    await test_session.flush()

    route = Route(
        code="ROUTE-TEST",
        name="Test Route",
        description="A route for testing",
    )
    test_session.add(route)
    await test_session.flush()

    vehicle = Vehicle(
        vehicle_code="BUS-TEST",
        route_id=route.id,
    )
    test_session.add(vehicle)
    await test_session.flush()

    assignment = Assignment(
        user_id=user.id,
        route_id=route.id,
        vehicle_id=vehicle.id,
        is_active=True,
    )
    test_session.add(assignment)
    await test_session.commit()

    # Query back
    result = await test_session.execute(select(User).where(User.email == "testdriver@example.com"))
    fetched_user = result.scalar_one()
    assert fetched_user.full_name == "Test Driver"
    assert len(fetched_user.assignments) == 1
    assert fetched_user.assignments[0].vehicle.vehicle_code == "BUS-TEST"


@pytest.mark.asyncio
async def test_single_active_assignment_constraint(test_session: AsyncSession):
    """
    Verify that a user can have only ONE active assignment, but CAN have historical inactive assignments.
    """
    user = User(
        email="multi@example.com",
        password_hash="hashed_pw",
        full_name="Multi Driver",
    )
    route1 = Route(code="R1", name="Route 1")
    route2 = Route(code="R2", name="Route 2")
    test_session.add_all([user, route1, route2])
    await test_session.flush()

    v1 = Vehicle(vehicle_code="V1", route_id=route1.id)
    v2 = Vehicle(vehicle_code="V2", route_id=route2.id)
    test_session.add_all([v1, v2])
    await test_session.flush()

    # First active assignment
    active1 = Assignment(
        user_id=user.id,
        route_id=route1.id,
        vehicle_id=v1.id,
        is_active=True,
    )
    test_session.add(active1)
    await test_session.commit()

    # Deactivate active1 -> convert to historical assignment
    active1.is_active = False
    await test_session.commit()

    # Create new active assignment -> should succeed because active1 is now False
    active2 = Assignment(
        user_id=user.id,
        route_id=route2.id,
        vehicle_id=v2.id,
        is_active=True,
    )
    test_session.add(active2)
    await test_session.commit()

    # Try inserting a second ACTIVE assignment for the same user while active2 is True -> MUST raise IntegrityError
    active_conflict = Assignment(
        user_id=user.id,
        route_id=route1.id,
        vehicle_id=v1.id,
        is_active=True,
    )
    test_session.add(active_conflict)
    with pytest.raises(IntegrityError):
        await test_session.commit()
    
    await test_session.rollback()


@pytest.mark.asyncio
async def test_seed_database_execution(test_session: AsyncSession):
    """
    Verify seed script populates deterministic data correctly.
    """
    await seed_database(test_session)

    # Verify User A
    user_a_stmt = select(User).where(User.email == "driver.a@example.com")
    user_a = (await test_session.execute(user_a_stmt)).scalar_one()
    assert user_a.full_name == "Driver Alice"
    assert len(user_a.assignments) == 1
    assert user_a.assignments[0].is_active is True
    assert user_a.assignments[0].route.code == "ROUTE-A"
    assert user_a.assignments[0].vehicle.vehicle_code == "BUS-001"

    # Verify User B
    user_b_stmt = select(User).where(User.email == "driver.b@example.com")
    user_b = (await test_session.execute(user_b_stmt)).scalar_one()
    assert user_b.full_name == "Driver Bob"
    assert len(user_b.assignments) == 1
    assert user_b.assignments[0].is_active is True
    assert user_b.assignments[0].route.code == "ROUTE-B"
    assert user_b.assignments[0].vehicle.vehicle_code == "BUS-002"

    # Verify route stops
    stops_a_stmt = select(RouteStop).join(Route).where(Route.code == "ROUTE-A").order_by(RouteStop.sequence)
    stops_a = (await test_session.execute(stops_a_stmt)).scalars().all()
    assert len(stops_a) == 6
    assert stops_a[0].name == "Central Station"

    # Idempotency check: running seed again should not duplicate data
    await seed_database(test_session)
    users = (await test_session.execute(select(User))).scalars().all()
    assert len(users) == 2
