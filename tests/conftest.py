
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_session
from app.main import app
from app.models.base import Base
from app.models.user import User
from app.core.security import get_password_hash
import pytest_asyncio

# Test database URL - use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_test_session() -> AsyncSession:
    """Get test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def setup_test_database():
    """Set up test database before each test."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create test user
    async with TestSessionLocal() as session:
        test_user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("testpass"),
            is_active=True,
            is_superuser=False
        )
        session.add(test_user)
        await session.commit()
    
    yield
    
    # Clean up after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    """Create async test client with database dependency override."""
    # Override the database dependency
    app.dependency_overrides[get_session] = get_test_session
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_session():
    """Get test database session for direct database operations."""
    async with TestSessionLocal() as session:
        yield session