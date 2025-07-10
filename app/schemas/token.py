"""Token schemas for OAuth2 authentication."""

from __future__ import annotations

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""
    username: str | None = None