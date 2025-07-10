"""Token schemas for OAuth2 authentication."""

from __future__ import annotations

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2 token response with both access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AccessTokenResponse(BaseModel):
    """Response schema for refresh token endpoint (only access token)."""
    access_token: str
    token_type: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token requests."""
    refresh_token: str


class TokenData(BaseModel):
    """Token payload data."""
    username: str | None = None