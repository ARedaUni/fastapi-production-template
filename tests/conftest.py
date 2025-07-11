import asyncio
from typing import Dict

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

from app.api.deps import get_session
from app.core.config import settings
from app.core.security import get_password_hash
from app.main import app
from app.models.base import Base
from app.models.user import User

# Use test database engine instead of production engine
test_engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture()
async def connection():
    async with test_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        # Clean up tables after test
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def session(connection: AsyncConnection):
    async with AsyncSession(connection, expire_on_commit=False) as _session:
        # Create test user for authentication tests
        test_user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("testpass"),
            is_active=True,
            is_superuser=False
        )
        _session.add(test_user)
        await _session.commit()
        yield _session


@pytest_asyncio.fixture(autouse=True)
async def override_dependency(session: AsyncSession):
    app.dependency_overrides[get_session] = lambda: session


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
        "username": "testuser",
        "password": "testpass",
    }
    res = await client.post("/api/v1/token", data=login_data)
    access_token = res.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}