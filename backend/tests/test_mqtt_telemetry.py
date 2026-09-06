import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.db.seed import seed_database
from app.models import GpsPoint, Vehicle
from app.schemas.mqtt import GpsTelemetryPayload
from app.services.telemetry_ingestion_service import TelemetryIngestionService
from app.services.vehicle_service import VehicleService, VehicleStatusEnum


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


# -------------------------------------------------------------------
# 1. Pydantic Payload Schema Bounds Validation Tests
# -------------------------------------------------------------------

def test_telemetry_schema_valid_payload():
    payload = {
        "latitude": 27.700769,
        "longitude": 85.300140,
        "speed": 25.5,
        "timestamp": "2026-09-06T14:00:00Z",
    }
    validated = GpsTelemetryPayload.model_validate(payload)
    assert validated.latitude == 27.700769
    assert validated.longitude == 85.300140
    assert validated.speed == 25.5
    assert validated.timestamp.tzinfo == timezone.utc


def test_telemetry_schema_out_of_bounds_latitude():
    payload = {
        "latitude": 127.700769, # Out of bounds > 90
        "longitude": 85.300140,
        "speed": 10.0,
        "timestamp": "2026-09-06T14:00:00Z",
    }
    with pytest.raises(ValidationError):
        GpsTelemetryPayload.model_validate(payload)


def test_telemetry_schema_negative_speed():
    payload = {
        "latitude": 27.700769,
        "longitude": 85.300140,
        "speed": -15.0, # Negative speed
        "timestamp": "2026-09-06T14:00:00Z",
    }
    with pytest.raises(ValidationError):
        GpsTelemetryPayload.model_validate(payload)


# -------------------------------------------------------------------
# 2. Ingestion & Out-of-Order Engine Tests
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ingest_valid_telemetry_packet(seeded_session: AsyncSession):
    """
    Verify valid telemetry packet appends GpsPoint history and updates Vehicle location state.
    """
    ingestion_service = TelemetryIngestionService(seeded_session)
    now = datetime.now(timezone.utc)
    payload = {
        "latitude": 27.702500,
        "longitude": 85.303100,
        "speed": 35.0,
        "timestamp": now.isoformat(),
    }

    success = await ingestion_service.process_payload("BUS-001", payload)
    assert success is True

    # Verify Vehicle current state was updated
    vehicle_stmt = select(Vehicle).where(Vehicle.vehicle_code == "BUS-001")
    vehicle = (await seeded_session.execute(vehicle_stmt)).scalar_one()
    assert vehicle.current_latitude == 27.702500
    assert vehicle.current_longitude == 85.303100
    assert vehicle.current_speed == 35.0

    # Verify GpsPoint history record was created
    gps_stmt = select(GpsPoint).where(GpsPoint.vehicle_id == vehicle.id)
    gps_points = (await seeded_session.execute(gps_stmt)).scalars().all()
    assert len(gps_points) >= 1


@pytest.mark.asyncio
async def test_out_of_order_stale_packet_protection(seeded_session: AsyncSession):
    """
    Out-of-Order Engine Test:
    Inject newer packet T2 = 14:10:00 (lat=27.705).
    Inject older packet T1 = 14:05:00 (lat=27.702).
    Assert T1 IS saved in gps_points history, BUT Vehicle.current_latitude remains T2 (27.705).
    """
    ingestion_service = TelemetryIngestionService(seeded_session)

    t2_newer = datetime(2026, 9, 6, 14, 10, 0, tzinfo=timezone.utc)
    t1_older = datetime(2026, 9, 6, 14, 5, 0, tzinfo=timezone.utc)

    payload_t2 = {
        "latitude": 27.705000,
        "longitude": 85.306000,
        "speed": 40.0,
        "timestamp": t2_newer.isoformat(),
    }
    payload_t1 = {
        "latitude": 27.702000,
        "longitude": 85.303000,
        "speed": 10.0,
        "timestamp": t1_older.isoformat(),
    }

    # Step 1: Ingest newer packet T2 first
    success_t2 = await ingestion_service.process_payload("BUS-001", payload_t2)
    assert success_t2 is True

    vehicle_stmt = select(Vehicle).where(Vehicle.vehicle_code == "BUS-001")
    vehicle = (await seeded_session.execute(vehicle_stmt)).scalar_one()
    v_latest = vehicle.latest_recorded_at.replace(tzinfo=timezone.utc) if vehicle.latest_recorded_at.tzinfo is None else vehicle.latest_recorded_at
    assert v_latest == t2_newer

    # Step 2: Ingest older packet T1 (out-of-order)
    success_t1 = await ingestion_service.process_payload("BUS-001", payload_t1)
    assert success_t1 is True

    # Re-query Vehicle -> Location state MUST REMAIN at T2 (27.705000)
    await seeded_session.refresh(vehicle)
    v_latest_after = vehicle.latest_recorded_at.replace(tzinfo=timezone.utc) if vehicle.latest_recorded_at.tzinfo is None else vehicle.latest_recorded_at
    assert vehicle.current_latitude == 27.705000
    assert v_latest_after == t2_newer, "Stale packet regressed latest_recorded_at!"

    # Verify BOTH points exist in GpsPoint history
    gps_stmt = select(GpsPoint).where(GpsPoint.vehicle_id == vehicle.id).order_by(GpsPoint.recorded_at)
    history = (await seeded_session.execute(gps_stmt)).scalars().all()
    recorded_times = [
        p.recorded_at.replace(tzinfo=timezone.utc) if p.recorded_at.tzinfo is None else p.recorded_at
        for p in history
    ]
    assert t1_older in recorded_times
    assert t2_newer in recorded_times


@pytest.mark.asyncio
async def test_unknown_vehicle_rejection(seeded_session: AsyncSession):
    """
    Verify packet for unknown vehicle code returns False and creates no DB records.
    """
    ingestion_service = TelemetryIngestionService(seeded_session)
    payload = {
        "latitude": 27.700000,
        "longitude": 85.300000,
        "speed": 0.0,
        "timestamp": "2026-09-06T14:00:00Z",
    }
    success = await ingestion_service.process_payload("BUS-UNKNOWN-999", payload)
    assert success is False


@pytest.mark.asyncio
async def test_vehicle_status_engine_calculation():
    """
    Verify VehicleStatusEngine rules: ACTIVE vs OFFLINE vs UNKNOWN.
    """
    now = datetime.now(timezone.utc)

    # 1. UNKNOWN when last_seen_at is None
    assert VehicleService.compute_vehicle_status(None, threshold_seconds=60) == VehicleStatusEnum.UNKNOWN

    # 2. ACTIVE when last_seen_at is 30 seconds ago (threshold 60s)
    recent = now - timedelta(seconds=30)
    assert VehicleService.compute_vehicle_status(recent, threshold_seconds=60) == VehicleStatusEnum.ACTIVE

    # 3. OFFLINE when last_seen_at is 120 seconds ago (threshold 60s)
    stale = now - timedelta(seconds=120)
    assert VehicleService.compute_vehicle_status(stale, threshold_seconds=60) == VehicleStatusEnum.OFFLINE
