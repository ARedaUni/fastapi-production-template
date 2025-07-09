"""Pydantic schemas for authentication tokens."""

from __future__ import annotations

from pydantic import BaseModel


class Token(BaseModel):
    """Response model for OAuth2 token."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Data contained within a JWT token."""
    username: str | None = None 