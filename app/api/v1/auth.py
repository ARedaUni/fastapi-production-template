"""Authentication endpoints."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.security import authenticate_user, create_access_token
from app.schemas.token import Token
from app.schemas.user import User

router = APIRouter(tags=["Authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Login endpoint that returns JWT access token."""
    user = authenticate_user(form_data.username, form_data.password)
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
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current authenticated user information."""
    return current_user 