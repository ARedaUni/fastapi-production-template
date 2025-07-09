"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.security import decode_access_token, get_user
from app.schemas.token import TokenData
from app.schemas.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(
        token, 
        settings.SECRET_KEY.get_secret_value(), 
        settings.ALGORITHM
    )
    if payload is None:
        raise credentials_exception
    
    username = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    token_data = TokenData(username=username)
    user_in_db = get_user(username=token_data.username)
    if user_in_db is None:
        raise credentials_exception
    
    # Return User without hashed_password
    return User(
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        disabled=user_in_db.disabled
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user (not disabled)."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 