"""Security utilities for password hashing and JWT tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User as UserModel
from app.schemas.user import User, UserInDB


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
    """Verify a plaintext password against its hash using bcrypt."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def decode_access_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any] | None:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.PyJWTError:
        return None


async def get_user(session: AsyncSession, username: str) -> UserInDB | None:
    """Get user from the database by username."""
    stmt = select(UserModel).where(UserModel.username == username)
    result = await session.execute(stmt)
    user_model = result.scalar_one_or_none()
    
    if not user_model:
        return None
    
    return UserInDB(
        username=user_model.username,
        email=user_model.email,
        full_name=user_model.full_name,
        disabled=not user_model.is_active,
        hashed_password=user_model.hashed_password
    )


async def user_exists(session: AsyncSession, username: str, email: str) -> dict[str, bool]:
    """Check if username or email already exists."""
    # Check username
    username_stmt = select(UserModel).where(UserModel.username == username)
    username_result = await session.execute(username_stmt)
    username_exists = username_result.scalar_one_or_none() is not None
    
    # Check email
    email_stmt = select(UserModel).where(UserModel.email == email)
    email_result = await session.execute(email_stmt)
    email_exists = email_result.scalar_one_or_none() is not None
    
    return {
        "username_exists": username_exists,
        "email_exists": email_exists
    }


async def authenticate_user(session: AsyncSession, username: str, password: str) -> User | None:
    """Authenticate a user with username and password."""
    user = await get_user(session, username)
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


async def create_user(session: AsyncSession, username: str, email: str, full_name: str, password: str) -> User:
    """Create a new user in the database."""
    hashed_password = get_password_hash(password)
    
    user_model = UserModel(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )
    
    session.add(user_model)
    await session.commit()
    await session.refresh(user_model)
    
    return User(
        username=user_model.username,
        email=user_model.email,
        full_name=user_model.full_name,
        disabled=not user_model.is_active
    )