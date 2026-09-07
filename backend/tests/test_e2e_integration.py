"""
End-to-End Integration Tests for GPS Finder System.

Tests the full lifecycle:
- Ingestion of MQTT Telemetry Packets
- Atomic DB Updates & Stale-Packet Protection
- Authorization & User-to-Vehicle Access Controls
- Location & History Querying (Date Filtering & Keyset Pagination)
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import ASGITransport, AsyncClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.db.seed import seed_database
from app.models import User
from app.main import create_app
from app.services.telemetry_ingestion_service import TelemetryIngestionService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


async def get_token_for_user(client: AsyncClient, email: str, password: str = "Password123!") -> str:
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# -------------------------------------------------------------------
# E2E Tests
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_e2e_telemetry_ingestion_to_api_read(
    async_client: AsyncClient,
    seeded_session: AsyncSession,
):
    """
    E2E Pipeline Test:
    1. Driver A logs in.
    2. Telemetry packet is ingested for BUS-001 (assigned to Driver A).
    3. GET /api/v1/me/vehicle/location reflects the new telemetry location and ACTIVE status.
    4. GET /api/v1/me/vehicle/history includes the ingested point.
    """
    token_a = await get_token_for_user(async_client, "driver.a@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    now = datetime.now(timezone.utc)
    ts = (now + timedelta(minutes=5)).isoformat()
    ingestion = TelemetryIngestionService(seeded_session)
    telemetry_payload = {
        "latitude": 27.710000,
        "longitude": 85.320000,
        "speed": 42.5,
        "timestamp": ts,
    }
    success = await ingestion.process_payload("BUS-001", telemetry_payload)
    assert success is True

    # Step 2: Query /me/vehicle/location via REST API
    loc_res = await async_client.get("/api/v1/me/vehicle/location", headers=headers_a)
    assert loc_res.status_code == 200
    loc_data = loc_res.json()
    assert loc_data["vehicle_code"] == "BUS-001"
    assert loc_data["latitude"] == 27.710000
    assert loc_data["longitude"] == 85.320000
    assert loc_data["speed"] == 42.5
    assert loc_data["status"] == "ACTIVE"

    # Step 3: Query /me/vehicle/history via REST API
    hist_res = await async_client.get("/api/v1/me/vehicle/history?limit=10", headers=headers_a)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data["items"]) >= 1
    top_item = hist_data["items"][0]
    assert top_item["latitude"] == 27.710000
    assert top_item["longitude"] == 85.320000
    assert top_item["speed"] == 42.5


@pytest.mark.asyncio
async def test_e2e_history_filtering_and_keyset_pagination(
    async_client: AsyncClient,
    seeded_session: AsyncSession,
):
    """
    Verify /api/v1/me/vehicle/history filtering by date range (from/to) and keyset pagination via cursor.
    """
    token_a = await get_token_for_user(async_client, "driver.a@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    ingestion = TelemetryIngestionService(seeded_session)

    # Ingest 5 points at 1-minute intervals
    timestamps = [
        "2026-09-06T10:00:00Z",
        "2026-09-06T10:01:00Z",
        "2026-09-06T10:02:00Z",
        "2026-09-06T10:03:00Z",
        "2026-09-06T10:04:00Z",
    ]
    for i, ts in enumerate(timestamps):
        payload = {
            "latitude": 27.700000 + (i * 0.001),
            "longitude": 85.300000 + (i * 0.001),
            "speed": 10.0 + i,
            "timestamp": ts,
        }
        await ingestion.process_payload("BUS-001", payload)

    # Query page 1 with limit=2
    res_p1 = await async_client.get("/api/v1/me/vehicle/history?limit=2", headers=headers_a)
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert len(data_p1["items"]) == 2
    assert data_p1["has_more"] is True
    assert data_p1["next_cursor"] is not None

    # Query page 2 using returned cursor
    cursor = data_p1["next_cursor"]
    res_p2 = await async_client.get(f"/api/v1/me/vehicle/history?limit=2&cursor={cursor}", headers=headers_a)
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert len(data_p2["items"]) == 2
    # Ensure items on page 2 are recorded before or equal to items on page 1 (descending order)
    assert data_p2["items"][0]["recorded_at"] <= data_p1["items"][-1]["recorded_at"]

    # Test date range filtering: from T=10:01:00Z to T=10:03:00Z
    t_from = "2026-09-06T10:01:00Z"
    t_to = "2026-09-06T10:03:00Z"
    res_filtered = await async_client.get(
        f"/api/v1/me/vehicle/history?from={t_from}&to={t_to}",
        headers=headers_a,
    )
    assert res_filtered.status_code == 200
    data_filtered = res_filtered.json()
    assert len(data_filtered["items"]) == 3  # T=10:01, 10:02, 10:03


@pytest.mark.asyncio
async def test_e2e_stale_packet_protection_via_api(
    async_client: AsyncClient,
    seeded_session: AsyncSession,
):
    """
    E2E Stale Packet Protection:
    1. Ingest packet at T2 = 12:00 (lat 27.708).
    2. Ingest packet at T1 = 11:30 (lat 27.701) [Out-of-Order].
    3. Location API must return T2's location (27.708).
    4. History API must contain both points in chronological DESC order.
    """
    token_a = await get_token_for_user(async_client, "driver.a@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    ingestion = TelemetryIngestionService(seeded_session)

    now = datetime.now(timezone.utc)
    t2_newer = (now + timedelta(minutes=10)).isoformat()
    t1_older = (now + timedelta(minutes=5)).isoformat()

    # Ingest newer packet first
    await ingestion.process_payload("BUS-001", {
        "latitude": 27.708000,
        "longitude": 85.308000,
        "speed": 50.0,
        "timestamp": t2_newer,
    })

    # Ingest older packet second (stale/out-of-order)
    await ingestion.process_payload("BUS-001", {
        "latitude": 27.701000,
        "longitude": 85.301000,
        "speed": 15.0,
        "timestamp": t1_older,
    })

    # Verify /me/vehicle/location retains T2's latest location
    loc_res = await async_client.get("/api/v1/me/vehicle/location", headers=headers_a)
    assert loc_res.status_code == 200
    loc_data = loc_res.json()
    assert loc_data["latitude"] == 27.708000
    assert loc_data["speed"] == 50.0

    # Verify /me/vehicle/history returns both points in DESC timestamp order
    hist_res = await async_client.get("/api/v1/me/vehicle/history", headers=headers_a)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    lats = [item["latitude"] for item in hist_data["items"]]
    assert lats[0] == 27.708000  # Newer point first
    assert 27.701000 in lats     # Older point present in history


@pytest.mark.asyncio
async def test_e2e_authorization_user_without_assignment(
    async_client: AsyncClient,
    seeded_session: AsyncSession,
):
    """
    Verify access control for users without an active vehicle assignment:
    - User with no active assignment accessing /me/vehicle/location returns 404 NO_ACTIVE_ASSIGNMENT.
    - User with no active assignment accessing /me/vehicle/history returns 404 NO_ACTIVE_ASSIGNMENT.
    """
    # Create unassigned user
    unassigned_user = User(
        email="unassigned.driver@example.com",
        password_hash=pwd_context.hash("Password123!"),
        full_name="Unassigned Driver",
        role="driver",
        is_active=True,
    )
    seeded_session.add(unassigned_user)
    await seeded_session.commit()

    token_unassigned = await get_token_for_user(async_client, "unassigned.driver@example.com")
    headers_u = {"Authorization": f"Bearer {token_unassigned}"}

    # GET /me/vehicle/location -> 404 NO_ACTIVE_ASSIGNMENT
    loc_res = await async_client.get("/api/v1/me/vehicle/location", headers=headers_u)
    assert loc_res.status_code == 404
    assert loc_res.json()["error"]["code"] == "NO_ACTIVE_ASSIGNMENT"

    # GET /me/vehicle/history -> 404 NO_ACTIVE_ASSIGNMENT
    hist_res = await async_client.get("/api/v1/me/vehicle/history", headers=headers_u)
    assert hist_res.status_code == 404
    assert hist_res.json()["error"]["code"] == "NO_ACTIVE_ASSIGNMENT"
