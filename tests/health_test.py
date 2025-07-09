import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.conftest import async_client


@pytest.mark.anyio
async def test_root(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200

