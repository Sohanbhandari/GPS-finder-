import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.db.seed import seed_database
from app.main import create_app
from app.models import Assignment, Route, User, Vehicle


@pytest_asyncio.fixture
async def test_engine():
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


@pytest_asyncio.fixture
async def seeded_session(test_session):
    await seed_database(test_session)
    yield test_session


@pytest_asyncio.fixture
async def async_client(seeded_session):
    app = create_app()

    async def _get_test_db():
        yield seeded_session

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def get_token_for_user(client: AsyncClient, email: str) -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return res.json()["access_token"]


@pytest.mark.asyncio
async def test_get_me_assignment_user_a(async_client: AsyncClient):
    """
    Verify User A resolves Route A and BUS-001 active assignment.
    """
    token_a = await get_token_for_user(async_client, "driver.a@example.com")
    headers = {"Authorization": f"Bearer {token_a}"}

    response = await async_client.get("/api/v1/me/assignment", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["is_active"] is True
    assert data["route"]["code"] == "ROUTE-A"
    assert data["vehicle"]["vehicle_code"] == "BUS-001"


@pytest.mark.asyncio
async def test_get_me_assignment_user_b(async_client: AsyncClient):
    """
    Verify User B resolves Route B and BUS-002 active assignment.
    """
    token_b = await get_token_for_user(async_client, "driver.b@example.com")
    headers = {"Authorization": f"Bearer {token_b}"}

    response = await async_client.get("/api/v1/me/assignment", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["is_active"] is True
    assert data["route"]["code"] == "ROUTE-B"
    assert data["vehicle"]["vehicle_code"] == "BUS-002"


@pytest.mark.asyncio
async def test_get_me_vehicle_user_a(async_client: AsyncClient):
    """
    Verify User A resolves assigned vehicle details for BUS-001.
    """
    token_a = await get_token_for_user(async_client, "driver.a@example.com")
    headers = {"Authorization": f"Bearer {token_a}"}

    response = await async_client.get("/api/v1/me/vehicle", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["vehicle_code"] == "BUS-001"
    assert "status" in data


@pytest.mark.asyncio
async def test_unauthorized_missing_token(async_client: AsyncClient):
    """
    Verify requesting protected endpoint without token returns 401 UNAUTHORIZED.
    """
    response = await async_client.get("/api/v1/me/assignment")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_cross_user_vehicle_access_denial(async_client: AsyncClient, seeded_session: AsyncSession):
    """
    Verify Server-Side Authorization: User B attempting to access User A's vehicle BUS-001 returns 403 VEHICLE_ACCESS_DENIED.
    """
    # Fetch BUS-001 ID
    vehicle_a_stmt = select(Vehicle).where(Vehicle.vehicle_code == "BUS-001")
    vehicle_a = (await seeded_session.execute(vehicle_a_stmt)).scalar_one()

    # Get User B token
    token_b = await get_token_for_user(async_client, "driver.b@example.com")
    headers = {"Authorization": f"Bearer {token_b}"}

    # User B requests BUS-001 explicitly -> MUST return 403 VEHICLE_ACCESS_DENIED
    response = await async_client.get(f"/api/v1/vehicles/{vehicle_a.id}", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "VEHICLE_ACCESS_DENIED"
    assert data["error"]["message"] == "You are not authorized to access this vehicle."


from app.core.security import get_password_hash

@pytest.mark.asyncio
async def test_no_active_assignment(async_client: AsyncClient, seeded_session: AsyncSession):
    """
    Verify user with no active assignment receives 404 NO_ACTIVE_ASSIGNMENT.
    """
    # Create User C with no active assignment
    user_c = User(
        email="driver.c@example.com",
        password_hash=get_password_hash("Password123!"),
        full_name="Driver Charlie",
        role="driver",
    )
    seeded_session.add(user_c)
    await seeded_session.commit()

    token_c = await get_token_for_user(async_client, "driver.c@example.com")
    headers = {"Authorization": f"Bearer {token_c}"}

    response = await async_client.get("/api/v1/me/assignment", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NO_ACTIVE_ASSIGNMENT"


@pytest.mark.asyncio
async def test_assignment_integrity_violation(async_client: AsyncClient, seeded_session: AsyncSession):
    """
    Verify backend rejects assignment where vehicle.route_id != assignment.route_id with 400 ASSIGNMENT_INTEGRITY_VIOLATION.
    """
    # Fetch User A, Route A, and Vehicle BUS-002 (which belongs to Route B)
    user_a_stmt = select(User).where(User.email == "driver.a@example.com")
    user_a = (await seeded_session.execute(user_a_stmt)).scalar_one()

    route_a_stmt = select(Route).where(Route.code == "ROUTE-A")
    route_a = (await seeded_session.execute(route_a_stmt)).scalar_one()

    vehicle_b_stmt = select(Vehicle).where(Vehicle.vehicle_code == "BUS-002")
    vehicle_b = (await seeded_session.execute(vehicle_b_stmt)).scalar_one()

    # Deactivate current assignment for User A
    active_a_stmt = select(Assignment).where(Assignment.user_id == user_a.id, Assignment.is_active == True)
    active_a = (await seeded_session.execute(active_a_stmt)).scalar_one()
    active_a.is_active = False

    # Insert corrupted assignment: User A -> Route A -> BUS-002 (BUS-002 route_id is Route B)
    corrupted = Assignment(
        user_id=user_a.id,
        route_id=route_a.id,
        vehicle_id=vehicle_b.id,
        is_active=True,
    )
    seeded_session.add(corrupted)
    await seeded_session.commit()

    token_a = await get_token_for_user(async_client, "driver.a@example.com")
    headers = {"Authorization": f"Bearer {token_a}"}

    response = await async_client.get("/api/v1/me/assignment", headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "ASSIGNMENT_INTEGRITY_VIOLATION"
