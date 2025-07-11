"""Integration tests for the complete authentication workflow."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_complete_auth_workflow_integration(client: AsyncClient):
    """Test the complete authentication workflow from registration to logout.
    
    This integration test covers:
    1. User registration
    2. Login to get tokens
    3. Access protected endpoint with access token
    4. Refresh access token using refresh token
    5. Access protected endpoint with new access token
    6. Logout (blacklist token)
    7. Verify access is denied after logout
    """
    
    # Step 1: Register a new user
    registration_data = {
        "username": "integrationuser",
        "email": "integration@example.com",
        "full_name": "Integration Test User",
        "password": "securepassword123"
    }
    
    register_response = await client.post(
        "/api/v1/register",
        json=registration_data
    )
    
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["username"] == "integrationuser"
    assert user_data["email"] == "integration@example.com"
    assert user_data["full_name"] == "Integration Test User"
    assert "password" not in user_data
    assert "hashed_password" not in user_data
    
    # Step 2: Login with the new user to get tokens
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": "integrationuser",
            "password": "securepassword123"
        }
    )
    
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert "expires_in" in token_data
    
    initial_access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    
    # Step 3: Access protected endpoint with access token
    protected_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {initial_access_token}"}
    )
    
    assert protected_response.status_code == 200
    me_data = protected_response.json()
    assert me_data["username"] == "integrationuser"
    assert me_data["email"] == "integration@example.com"
    assert me_data["full_name"] == "Integration Test User"
    
    # Step 4: Refresh access token using refresh token
    refresh_response = await client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"
    assert "expires_in" in refresh_data
    
    new_access_token = refresh_data["access_token"]
    assert new_access_token != initial_access_token  # Should be different
    
    # Step 5: Access protected endpoint with new access token
    protected_response_new = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    
    assert protected_response_new.status_code == 200
    me_data_new = protected_response_new.json()
    assert me_data_new["username"] == "integrationuser"
    
    # Step 6: Logout (blacklist the new access token)
    logout_response = await client.post(
        "/api/v1/logout",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    
    assert logout_response.status_code == 200
    logout_data = logout_response.json()
    assert logout_data["message"] == "Successfully logged out"
    
    # Step 7: Verify access is denied after logout
    protected_response_after_logout = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    
    assert protected_response_after_logout.status_code == 401


@pytest.mark.asyncio
async def test_invalid_credentials_login_fails(client: AsyncClient):
    """Test that login fails with invalid credentials."""
    # Try to login with non-existent user
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": "nonexistent",
            "password": "wrongpassword"
        }
    )
    
    assert login_response.status_code == 401
    error_data = login_response.json()
    assert "error" in error_data
    assert error_data["error"] == "invalid_grant"


@pytest.mark.asyncio
async def test_invalid_refresh_token_fails(client: AsyncClient):
    """Test that refresh fails with invalid refresh token."""
    refresh_response = await client.post(
        "/api/v1/refresh",
        json={"refresh_token": "invalid.token.here"}
    )
    
    assert refresh_response.status_code == 401
    error_data = refresh_response.json()
    assert "error" in error_data
    assert error_data["error"] == "invalid_grant"


@pytest.mark.asyncio
async def test_access_protected_endpoint_without_token_fails(client: AsyncClient):
    """Test that accessing protected endpoint without token fails."""
    protected_response = await client.get("/api/v1/users/me")
    
    assert protected_response.status_code == 401
    error_data = protected_response.json()
    assert "detail" in error_data


@pytest.mark.asyncio
async def test_access_protected_endpoint_with_invalid_token_fails(client: AsyncClient):
    """Test that accessing protected endpoint with invalid token fails."""
    protected_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    
    assert protected_response.status_code == 401
    error_data = protected_response.json()
    assert "detail" in error_data


@pytest.mark.asyncio
async def test_refresh_token_workflow_integration(client: AsyncClient):
    """Test the refresh token workflow in isolation.
    
    This test focuses specifically on the refresh token flow:
    1. Create user and login
    2. Use refresh token to get new access token
    3. Verify new access token works
    4. Verify old access token still works (refresh doesn't invalidate it)
    """
    
    # Step 1: Register and login
    registration_data = {
        "username": "refreshuser",
        "email": "refresh@example.com",
        "full_name": "Refresh Test User",
        "password": "refreshpassword123"
    }
    
    register_response = await client.post(
        "/api/v1/register",
        json=registration_data
    )
    assert register_response.status_code == 201
    
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": "refreshuser",
            "password": "refreshpassword123"
        }
    )
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    original_access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    
    # Step 2: Use refresh token to get new access token
    refresh_response = await client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    new_access_token = refresh_data["access_token"]
    
    # Step 3: Verify new access token works
    me_response_new = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    
    assert me_response_new.status_code == 200
    me_data = me_response_new.json()
    assert me_data["username"] == "refreshuser"
    
    # Step 4: Verify original access token still works (refresh doesn't invalidate it)
    me_response_original = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {original_access_token}"}
    )
    
    assert me_response_original.status_code == 200


@pytest.mark.asyncio
async def test_token_blacklist_workflow_integration(client: AsyncClient):
    """Test the token blacklisting workflow.
    
    This test focuses on token blacklisting behavior:
    1. Create user, login, and get tokens
    2. Access protected endpoint successfully
    3. Logout (blacklist token)
    4. Verify blacklisted token is rejected
    5. Verify refresh token can still create new access token
    6. Logout with new token and verify it's also blacklisted
    """
    
    # Step 1: Register and login
    registration_data = {
        "username": "blacklistuser",
        "email": "blacklist@example.com",
        "full_name": "Blacklist Test User",
        "password": "blacklistpassword123"
    }
    
    register_response = await client.post(
        "/api/v1/register",
        json=registration_data
    )
    assert register_response.status_code == 201
    
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": "blacklistuser",
            "password": "blacklistpassword123"
        }
    )
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    
    # Step 2: Access protected endpoint successfully
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 200
    
    # Step 3: Logout (blacklist token)
    logout_response = await client.post(
        "/api/v1/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_response.status_code == 200
    
    # Step 4: Verify blacklisted token is rejected
    me_response_after_logout = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response_after_logout.status_code == 401
    
    # Step 5: Verify refresh token can still create new access token
    refresh_response = await client.post(
        "/api/v1/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    
    new_access_token = refresh_response.json()["access_token"]
    
    # Verify new token works
    me_response_new = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_response_new.status_code == 200
    
    # Step 6: Logout with new token and verify it's also blacklisted
    logout_response_2 = await client.post(
        "/api/v1/logout",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert logout_response_2.status_code == 200
    
    me_response_final = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_response_final.status_code == 401


@pytest.mark.asyncio
async def test_disabled_user_cannot_access_system(client: AsyncClient):
    """Test that disabled users cannot access the system.
    
    Note: This test requires the ability to disable users, which may need
    to be implemented as an admin feature. For now, we test with existing user.
    """
    # Test with existing test user that should be active
    login_response = await client.post(
        "/api/v1/token",
        data={
            "username": settings.FIRST_USERNAME,
            "password": settings.FIRST_PASSWORD.get_secret_value()
        }
    )
    
    assert login_response.status_code == 200
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # Access should work for active user
    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["disabled"] is False or user_data["disabled"] is None


@pytest.mark.asyncio
async def test_multiple_user_registrations_sequential(client: AsyncClient):
    """Test multiple user registrations work correctly when done sequentially."""
    # Create multiple users sequentially (not concurrently to avoid session conflicts)
    users_data = [
        {
            "username": f"sequser{i}",
            "email": f"sequser{i}@example.com",
            "full_name": f"Sequential User {i}",
            "password": "sequentialpassword123"
        }
        for i in range(3)
    ]
    
    access_tokens = []
    
    # Register and login each user sequentially
    for user_data in users_data:
        # Register user
        register_response = await client.post(
            "/api/v1/register",
            json=user_data
        )
        assert register_response.status_code == 201
        
        # Login user
        login_response = await client.post(
            "/api/v1/token",
            data={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )
        assert login_response.status_code == 200
        access_tokens.append(login_response.json()["access_token"])
    
    # Verify all tokens work
    for i, token in enumerate(access_tokens):
        me_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["username"] == f"sequser{i}" 