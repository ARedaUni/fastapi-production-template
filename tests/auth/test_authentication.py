"""Tests for OAuth2 authentication system."""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_login_with_valid_credentials(client):
    """Test that login with valid credentials returns access token."""
    # Using form data as per OAuth2 password flow
    response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_returns_refresh_token(client):
    """Test that login with valid credentials returns both access and refresh tokens."""
    response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value(),
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify we get both tokens
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    # Verify expires_in field
    assert "expires_in" in data
    assert isinstance(data["expires_in"], int)
    assert data["expires_in"] == 1800  # 30 minutes in seconds

    # Both tokens should be non-empty strings
    assert isinstance(data["access_token"], str)
    assert isinstance(data["refresh_token"], str)
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0

    # Tokens should be different
    assert data["access_token"] != data["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_token_gets_new_access_token(client):
    """Test that refresh token can be used to get a new access token."""
    # First login to get tokens
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value(),
        },
    )

    assert login_response.status_code == 200
    login_data = login_response.json()
    original_access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # Use refresh token to get new access token
    refresh_response = await client.post(
        "/api/v1/refresh", json={"refresh_token": refresh_token}
    )

    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()

    # Verify response structure
    assert "access_token" in refresh_data
    assert "token_type" in refresh_data
    assert refresh_data["token_type"] == "bearer"

    # Verify expires_in field in refresh response
    assert "expires_in" in refresh_data
    assert isinstance(refresh_data["expires_in"], int)
    assert refresh_data["expires_in"] == 1800  # 30 minutes in seconds

    # New access token should be different from original
    new_access_token = refresh_data["access_token"]
    assert isinstance(new_access_token, str)
    assert len(new_access_token) > 0
    assert new_access_token != original_access_token


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_fails(client):
    """Test that using an invalid refresh token returns OAuth2 error format."""
    response = await client.post(
        "/api/v1/refresh", json={"refresh_token": "invalid_refresh_token"}
    )

    assert response.status_code == 401
    data = response.json()

    # Should return OAuth2 error format
    assert "error" in data
    assert "error_description" in data
    assert data["error"] == "invalid_grant"
    assert "Invalid refresh token" in data["error_description"]


@pytest.mark.asyncio
async def test_login_missing_parameters_returns_oauth2_error(client):
    """Test that login with missing parameters returns OAuth2 invalid_request error."""
    response = await client.post(
        "/api/v1/token",
        data={"username": settings.FIRST_USERNAME},  # Missing password
    )

    assert response.status_code == 400
    data = response.json()

    # Should return OAuth2 error format for missing required parameters
    assert "error" in data
    assert "error_description" in data
    assert data["error"] == "invalid_request"
    assert "password" in data["error_description"].lower()


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client):
    """Test that using an access token as refresh token returns 401."""
    # First login to get tokens
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value(),
        },
    )

    assert login_response.status_code == 200
    login_data = login_response.json()
    access_token = login_data["access_token"]  # This is an access token, not refresh

    # Try to use access token as refresh token (should fail)
    refresh_response = await client.post(
        "/api/v1/refresh", json={"refresh_token": access_token}
    )

    assert refresh_response.status_code == 401
    data = refresh_response.json()

    # Should return OAuth2 error format
    assert "error" in data
    assert "error_description" in data
    assert data["error"] == "invalid_grant"
    assert "Invalid refresh token" in data["error_description"]


@pytest.mark.asyncio
async def test_access_protected_route_with_refresh_token_fails(client):
    """Test that refresh token cannot be used to access protected routes."""
    # First login to get tokens
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value(),
        },
    )

    assert login_response.status_code == 200
    login_data = login_response.json()
    refresh_token = login_data["refresh_token"]

    # Try to access protected route with refresh token (should fail)
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {refresh_token}"}
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_login_with_invalid_credentials(client):
    """Test that login with invalid credentials returns OAuth2 error format."""
    response = await client.post(
        "/api/v1/token", data={"username": "wronguser", "password": "wrongpass"}
    )

    assert response.status_code == 401
    data = response.json()

    # Should return OAuth2 error format instead of FastAPI's default
    assert "error" in data
    assert "error_description" in data
    assert data["error"] == "invalid_grant"
    assert "Invalid username or password" in data["error_description"]


@pytest.mark.asyncio
async def test_access_protected_route_with_valid_token(client):
    """Test that protected route works with valid bearer token."""
    # First login to get token
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value(),
        },
    )
    token = login_response.json()["access_token"]

    # Access protected route
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["username"] == settings.FIRST_USERNAME


@pytest.mark.asyncio
async def test_access_protected_route_without_token(client):
    """Test that protected route returns 401 without token."""
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_access_protected_route_with_invalid_token(client):
    """Test that protected route returns 401 with invalid token."""
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_token_has_correct_structure(client):
    """Test that token response has correct structure."""
    response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value(),
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Required OAuth2 fields
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    # Token should be a string with reasonable length
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 10


@pytest.mark.asyncio
async def test_logout_endpoint_exists_and_requires_authentication(client):
    """Test that logout endpoint exists and requires authentication."""
    response = await client.post("/api/v1/logout")

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_logout_invalidates_current_token(client):
    """Test that logout properly invalidates the current token."""
    # First login to get token
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value(),
        },
    )
    token = login_response.json()["access_token"]

    # Verify token works
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Logout
    logout_response = await client.post(
        "/api/v1/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_response.status_code == 200

    # Try to use token again (should fail)
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
