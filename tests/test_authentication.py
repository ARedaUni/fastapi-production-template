"""Tests for OAuth2 authentication system."""

import pytest


@pytest.mark.anyio
async def test_login_with_valid_credentials(async_client):
    """Test that login with valid credentials returns access token."""
    # Using form data as per OAuth2 password flow
    response = await async_client.post(
        "/api/v1/token",
        data={"username": "testuser", "password": "testpass"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_with_invalid_credentials(async_client):
    """Test that login with invalid credentials returns 401."""
    response = await async_client.post(
        "/api/v1/token",
        data={"username": "wronguser", "password": "wrongpass"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_access_protected_route_with_valid_token(async_client):
    """Test that protected route works with valid bearer token."""
    # First login to get token
    login_response = await async_client.post(
        "/api/v1/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    
    # Access protected route
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["username"] == "testuser"


@pytest.mark.anyio
async def test_access_protected_route_without_token(async_client):
    """Test that protected route returns 401 without token."""
    response = await async_client.get("/api/v1/users/me")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_access_protected_route_with_invalid_token(async_client):
    """Test that protected route returns 401 with invalid token."""
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_token_has_correct_structure(async_client):
    """Test that token response has correct structure."""
    response = await async_client.post(
        "/api/v1/token",
        data={"username": "testuser", "password": "testpass"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify required fields
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    
    # Token should be a non-empty string
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0 