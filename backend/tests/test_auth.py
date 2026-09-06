import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.db.seed import seed_database
from app.main import create_app


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


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """
    Verify POST /api/v1/auth/login returns JWT token for valid credentials.
    """
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "driver.a@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    """
    Verify POST /api/v1/auth/login returns 401 INVALID_CREDENTIALS for wrong password.
    """
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "driver.a@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """
    Verify POST /api/v1/auth/login returns 401 INVALID_CREDENTIALS for unknown email.
    """
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "Password123!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
