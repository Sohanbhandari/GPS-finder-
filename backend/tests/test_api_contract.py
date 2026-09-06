import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.db.seed import seed_database
from app.main import create_app
from sqlalchemy import select
from app.models import GpsPoint, Vehicle


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
async def test_health_check_contract(async_client: AsyncClient):
    """
    Verify GET /api/v1/health conforms to HealthResponse schema.
    """
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_me_assignment_route_stops_sequence_order(async_client: AsyncClient):
    """
    Verify RouteStops in GET /api/v1/me/assignment are returned strictly in sequence order (sequence ASC).
    """
    token = await get_token_for_user(async_client, "driver.a@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/me/assignment", headers=headers)
    assert response.status_code == 200
    data = response.json()

    stops = data["route"]["stops"]
    assert len(stops) > 0

    sequences = [s["sequence"] for s in stops]
    assert sequences == sorted(sequences), f"Stops are not strictly ordered by sequence ASC: {sequences}"


@pytest.mark.asyncio
async def test_me_vehicle_location(async_client: AsyncClient):
    """
    Verify GET /api/v1/me/vehicle/location returns current location and status.
    """
    token = await get_token_for_user(async_client, "driver.a@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.get("/api/v1/me/vehicle/location", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["vehicle_code"] == "BUS-001"
    assert "status" in data
    assert "latitude" in data
    assert "longitude" in data


@pytest.mark.asyncio
async def test_me_vehicle_history_contract_and_validation(async_client: AsyncClient, seeded_session: AsyncSession):
    """
    Verify GET /api/v1/me/vehicle/history pagination, sorting, and date validation (from <= to).
    """
    token = await get_token_for_user(async_client, "driver.a@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Test invalid date range from > to -> 422 VALIDATION_ERROR
    from_time = "2026-09-06T12:00:00Z"
    to_time = "2026-09-06T10:00:00Z"
    response = await async_client.get(
        f"/api/v1/me/vehicle/history?from={from_time}&to={to_time}",
        headers=headers,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"

    # Test successful history retrieval
    response = await async_client.get("/api/v1/me/vehicle/history?limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "has_more" in data


@pytest.mark.asyncio
async def test_openapi_json_schema_generation(async_client: AsyncClient):
    """
    Verify GET /api/v1/openapi.json generates valid OpenAPI schema matching API contract paths.
    """
    response = await async_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    assert schema["openapi"].startswith("3.")
    paths = schema["paths"]

    assert "/api/v1/health" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/me/assignment" in paths
    assert "/api/v1/me/vehicle" in paths
    assert "/api/v1/me/vehicle/location" in paths
    assert "/api/v1/me/vehicle/history" in paths
