"""Tests for user registration system."""

import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_register_new_user_success(client):
    """Test that registering a new user with valid data returns success."""
    registration_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "securepassword123"
    }

    response = await client.post(
        "/api/v1/register",
        json=registration_data
    )

    assert response.status_code == 201
    data = response.json()

    # Verify response contains user data without password
    assert "username" in data
    assert "email" in data
    assert "full_name" in data
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"

    # Ensure password is not in response
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username_fails(client):
    """Test that registering with an existing username returns 400 error."""
    registration_data = {
        "username": settings.FIRST_USERNAME,  # This username already exists in test data
        "email": "different@example.com",
        "full_name": "Different User",
        "password": "securepassword123"
    }

    response = await client.post(
        "/api/v1/register",
        json=registration_data
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Username already registered" in data["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client):
    """Test that registering with an existing email returns 400 error."""
    registration_data = {
        "username": "differentuser",
        "email": "test@example.com",  # This email already exists in test data
        "full_name": "Different User",
        "password": "securepassword123"
    }

    response = await client.post(
        "/api/v1/register",
        json=registration_data
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Email already registered" in data["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email_fails(client):
    """Test that registering with invalid email format returns 422 validation error."""
    registration_data = {
        "username": "newuser",
        "email": "not-an-email",
        "full_name": "New User",
        "password": "securepassword123"
    }

    response = await client.post(
        "/api/v1/register",
        json=registration_data
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_short_password_fails(client):
    """Test that registering with password shorter than 8 characters fails."""
    registration_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "short"  # Less than 8 characters
    }

    response = await client.post(
        "/api/v1/register",
        json=registration_data
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_short_username_fails(client):
    """Test that registering with username shorter than 3 characters fails."""
    registration_data = {
        "username": "ab",  # Less than 3 characters
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "securepassword123"
    }

    response = await client.post(
        "/api/v1/register",
        json=registration_data
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_register_empty_full_name_fails(client):
    """Test that registering with empty full name fails."""
    registration_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "",  # Empty full name
        "password": "securepassword123"
    }

    response = await client.post(
        "/api/v1/register",
        json=registration_data
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_registered_user_can_login(client):
    """Test that a newly registered user can immediately login."""
    # First register a new user
    registration_data = {
        "username": "loginuser",
        "email": "loginuser@example.com",
        "full_name": "Login User",
        "password": "loginpassword123"
    }

    register_response = await client.post(
        "/api/v1/register",
        json=registration_data
    )

    assert register_response.status_code == 201

    # Now try to login with the new user
    login_response = await client.post(
        "/api/v1/token",
        data={"username": "loginuser", "password": "loginpassword123"}
    )

    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert "token_type" in login_data
    assert login_data["token_type"] == "bearer"
