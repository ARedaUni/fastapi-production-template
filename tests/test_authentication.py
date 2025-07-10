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
async def test_login_returns_refresh_token(async_client):
    """Test that login with valid credentials returns both access and refresh tokens."""
    response = await async_client.post(
        "/api/v1/token",
        data={"username": "testuser", "password": "testpass"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify we get both tokens
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    
    # Both tokens should be non-empty strings
    assert isinstance(data["access_token"], str)
    assert isinstance(data["refresh_token"], str)
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0
    
    # Tokens should be different
    assert data["access_token"] != data["refresh_token"]


@pytest.mark.anyio
async def test_refresh_token_gets_new_access_token(async_client):
    """Test that refresh token can be used to get a new access token."""
    # First login to get tokens
    login_response = await async_client.post(
        "/api/v1/token",
        data={"username": "testuser", "password": "testpass"}
    )
    
    assert login_response.status_code == 200
    login_data = login_response.json()
    original_access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]
    
    # Use refresh token to get new access token
    refresh_response = await async_client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    
    # Verify response structure
    assert "access_token" in refresh_data
    assert "token_type" in refresh_data
    assert refresh_data["token_type"] == "bearer"
    
    # New access token should be different from original
    new_access_token = refresh_data["access_token"]
    assert isinstance(new_access_token, str)
    assert len(new_access_token) > 0
    assert new_access_token != original_access_token


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