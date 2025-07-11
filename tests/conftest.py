import asyncio
from typing import Dict

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from slowapi import Limiter
from fastapi import Request
from pytest_postgresql import factories

from app.api.deps import get_session
from app.core.config import settings
from app.core.security import get_password_hash
from app.main import app
from app.models.base import Base
from app.models.user import User

# Create PostgreSQL test factories
postgresql_proc = factories.postgresql_proc(
    port=None,
    unixsocketdir='/tmp'
)
postgresql = factories.postgresql('postgresql_proc')

# Create a test limiter with no limits
def get_test_client_ip(request: Request) -> str:
    """Test rate limiter that doesn't actually limit."""
    return "test-client"

test_limiter = Limiter(
    key_func=get_test_client_ip,
    default_limits=["999999/minute"] 
)


@pytest_asyncio.fixture()
async def connection(postgresql):
    """Create test database connection using pytest-postgresql."""
    # Create async engine using the pytest-postgresql instance
    database_url = (
        f"postgresql+asyncpg://"
        f"{postgresql.info.user}@"
        f"{postgresql.info.host}:"
        f"{postgresql.info.port}/"
        f"{postgresql.info.dbname}"
    )
    
    engine = create_async_engine(database_url, echo=False)
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        # Clean up tables after test
        await conn.run_sync(Base.metadata.drop_all)
    
    # Close the engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def session(connection: AsyncConnection):
    async with AsyncSession(connection, expire_on_commit=False) as _session:
        # Create test user for authentication tests using settings
        test_user = User(
            username=settings.FIRST_USERNAME,
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash(settings.FIRST_PASSWORD.get_secret_value()),
            is_active=True,
            is_superuser=False
        )
        _session.add(test_user)
        await _session.commit()
        yield _session


@pytest_asyncio.fixture(autouse=True)
async def override_dependency(session: AsyncSession):
    # Override database dependency
    app.dependency_overrides[get_session] = lambda: session
    
    # Override rate limiter for tests
    original_limiter = app.state.limiter
    app.state.limiter = test_limiter
    
    yield
    
    # Restore original limiter after test
    app.state.limiter = original_limiter


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Reference: https://github.com/pytest-dev/pytest-asyncio/issues/38#issuecomment-264418154"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac, LifespanManager(app):
        yield ac


@pytest_asyncio.fixture()
async def superuser_token_headers(client: AsyncClient) -> Dict[str, str]:
    login_data = {
        "username": settings.FIRST_USERNAME,
        "password": settings.FIRST_PASSWORD.get_secret_value(),
    }
    res = await client.post("/api/v1/token", data=login_data)
    access_token = res.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}