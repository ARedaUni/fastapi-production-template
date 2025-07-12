"""Security utilities for password hashing and JWT tokens."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User as UserModel
from app.schemas.user import User, UserInDB


class TokenBlacklist:
    """Simple in-memory token blacklist service."""

    def __init__(self) -> None:
        self._blacklisted_tokens: set[str] = set()

    def blacklist_token(self, jti: str) -> None:
        """Add a token JTI to the blacklist."""
        self._blacklisted_tokens.add(jti)

    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        return jti in self._blacklisted_tokens


# Global instance - in production this should be Redis or database
_token_blacklist = TokenBlacklist()


def get_token_blacklist() -> TokenBlacklist:
    """Get the token blacklist service."""
    return _token_blacklist


class OAuth2Error(Exception):
    """OAuth2 compliant error exception."""

    def __init__(self, error: str, error_description: str, status_code: int = 400):
        self.error = error
        self.error_description = error_description
        self.status_code = status_code
        super().__init__(error_description)


class TokenType(str, Enum):
    """Token type enumeration."""

    ACCESS = "access"
    REFRESH = "refresh"


class TokenService:
    """Service for creating and validating JWT tokens."""

    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def _create_token(
        self,
        user: User,
        token_type: TokenType,
        expires_delta: timedelta,
        jti_length: int = 8,
    ) -> str:
        """Create a JWT token with common logic."""
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {
            "sub": user.username,
            "type": token_type.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(jti_length),
        }

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_access_token(
        self,
        user: User,
        expires_delta: timedelta | None = None,
        default_expire_minutes: int = 30,
    ) -> str:
        """Create a JWT access token for a user."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=default_expire_minutes)

        return self._create_token(user, TokenType.ACCESS, expires_delta, jti_length=8)

    def create_refresh_token(
        self,
        user: User,
        expires_delta: timedelta | None = None,
        default_expire_days: int = 7,
    ) -> str:
        """Create a JWT refresh token for a user."""
        if expires_delta is None:
            expires_delta = timedelta(days=default_expire_days)

        return self._create_token(user, TokenType.REFRESH, expires_delta, jti_length=16)

    def _decode_token(
        self, token: str, expected_type: TokenType
    ) -> dict[str, Any] | None:
        """Decode and validate a JWT token with common logic."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Ensure payload is a dict (jwt.decode can return Any)
            if not isinstance(payload, dict):
                return None

            # Verify token type
            if payload.get("type") != expected_type.value:
                return None

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and get_token_blacklist().is_blacklisted(jti):
                return None

            return payload
        except jwt.PyJWTError:
            return None

    def decode_access_token(self, token: str) -> dict[str, Any] | None:
        """Decode and verify a JWT access token."""
        return self._decode_token(token, TokenType.ACCESS)

    def decode_refresh_token(self, token: str) -> dict[str, Any] | None:
        """Decode and verify a JWT refresh token."""
        return self._decode_token(token, TokenType.REFRESH)


def get_token_service() -> TokenService:
    """Get configured TokenService instance."""
    from app.core.config import settings

    return TokenService(
        secret_key=settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash using bcrypt."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def convert_user_model_to_schema(user_model: UserModel) -> UserInDB:
    """Convert UserModel to UserInDB schema."""
    return UserInDB(
        username=user_model.username,
        email=user_model.email,
        full_name=user_model.full_name,
        disabled=not user_model.is_active,
        hashed_password=user_model.hashed_password,
    )


def convert_user_in_db_to_user(user_in_db: UserInDB) -> User:
    """Convert UserInDB to User schema (without password)."""
    return User(
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        disabled=user_in_db.disabled,
    )


async def get_user(session: AsyncSession, username: str) -> UserInDB | None:
    """Get user from the database by username."""
    stmt = select(UserModel).where(UserModel.username == username)
    result = await session.execute(stmt)
    user_model = result.scalar_one_or_none()

    if not user_model:
        return None

    return convert_user_model_to_schema(user_model)


async def user_exists(
    session: AsyncSession, username: str, email: str
) -> dict[str, bool]:
    """Check if username or email already exists."""
    # Check username
    username_stmt = select(UserModel).where(UserModel.username == username)
    username_result = await session.execute(username_stmt)
    username_exists = username_result.scalar_one_or_none() is not None

    # Check email
    email_stmt = select(UserModel).where(UserModel.email == email)
    email_result = await session.execute(email_stmt)
    email_exists = email_result.scalar_one_or_none() is not None

    return {"username_exists": username_exists, "email_exists": email_exists}


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """Authenticate a user with username and password."""
    user = await get_user(session, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.disabled:
        return None

    return convert_user_in_db_to_user(user)


async def create_user(
    session: AsyncSession, username: str, email: str, full_name: str, password: str
) -> User:
    """Create a new user in the database."""
    hashed_password = get_password_hash(password)

    user_model = UserModel(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
    )

    session.add(user_model)
    await session.commit()
    await session.refresh(user_model)

    return convert_user_in_db_to_user(convert_user_model_to_schema(user_model))
