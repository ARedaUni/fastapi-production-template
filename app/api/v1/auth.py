"""Authentication endpoints."""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_session
from app.core.security import (
    OAuth2Error,
    authenticate_user,
    convert_user_in_db_to_user,
    create_user,
    get_token_blacklist,
    get_token_service,
    get_user,
    user_exists,
)
from app.schemas.token import AccessTokenResponse, RefreshTokenRequest, Token
from app.schemas.user import User, UserCreate

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    """Register a new user."""
    # Check if username or email already exists
    existing = await user_exists(session, user_data.username, user_data.email)

    if existing["username_exists"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    if existing["email_exists"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    user = await create_user(
        session=session,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password=user_data.password,
    )

    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Token:
    """Login endpoint that returns access and refresh tokens."""
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise OAuth2Error(
            error="invalid_grant",
            error_description="Invalid username or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token_service = get_token_service()

    # Create both tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token_service.create_access_token(
        user=user, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = token_service.create_refresh_token(
        user=user, expires_delta=refresh_token_expires
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AccessTokenResponse:
    """Use refresh token to get a new access token."""

    token_service = get_token_service()

    # Decode and validate refresh token
    payload = token_service.decode_refresh_token(refresh_request.refresh_token)
    if payload is None:
        raise OAuth2Error(
            error="invalid_grant",
            error_description="Invalid refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    username = payload.get("sub")
    if username is None or not isinstance(username, str):
        raise OAuth2Error(
            error="invalid_grant",
            error_description="Invalid refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Get user from database
    user = await get_user(session, username)
    if user is None:
        raise OAuth2Error(
            error="invalid_grant",
            error_description="Invalid refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = token_service.create_access_token(
        user=convert_user_in_db_to_user(user), expires_delta=access_token_expires
    )

    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Logout the current user by invalidating their token."""
    # Extract JTI from token and blacklist it
    token_service = get_token_service()
    payload = token_service.decode_access_token(token)

    if payload and payload.get("jti"):
        blacklist = get_token_blacklist()
        blacklist.blacklist_token(payload["jti"])

    return {"message": "Successfully logged out"}


@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user profile."""
    return current_user
