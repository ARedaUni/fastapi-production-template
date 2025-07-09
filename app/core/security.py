"""Security utilities for password hashing and JWT tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.schemas.user import User, UserInDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple in-memory user database for testing
# In production, this would be replaced with database queries
fake_users_db = {
    "testuser": UserInDB(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        disabled=False,
        hashed_password="$2b$12$7kNiLErBvtTiMPSTDj28Aef46.xEiN1M2vzKLJo5U/F4nEqTtRUmm"  # "testpass"
    )
}


def create_access_token(user: User, secret_key: str, algorithm: str, expires_delta: timedelta | None = None, default_expire_minutes: int = 30) -> str:
    """Create a JWT access token for a user."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=default_expire_minutes)
    
    to_encode = {"sub": user.username, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def decode_access_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any] | None:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.PyJWTError:
        return None


def get_user(username: str) -> UserInDB | None:
    """Get user from the database by username."""
    return fake_users_db.get(username)


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a user with username and password."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.disabled:
        return None
    
    # Return User without hashed_password
    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled
    ) 