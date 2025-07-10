"""Authentication endpoints."""

from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.schemas.token import Token
from app.schemas.user import User, UserCreate
from app.core.security import authenticate_user, create_access_token, decode_access_token, get_user, create_user, user_exists

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token, settings.SECRET_KEY.get_secret_value(), settings.ALGORITHM)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = await get_user(session, username)
    if user is None:
        raise credentials_exception
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Return User without hashed_password
    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled
    )


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    """Register a new user."""
    # Check if username or email already exists
    existing = await user_exists(session, user_data.username, user_data.email)
    
    if existing["username_exists"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if existing["email_exists"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = await create_user(
        session=session,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        password=user_data.password
    )
    
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Token:
    """Login endpoint that returns an access token."""
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user=user,
        secret_key=settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
        expires_delta=access_token_expires,
        default_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get current user profile."""
    return current_user