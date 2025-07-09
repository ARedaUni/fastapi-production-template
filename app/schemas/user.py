"""Pydantic schemas for user models."""

from __future__ import annotations

from pydantic import BaseModel


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class User(UserBase):
    """User schema for responses (without password)."""
    pass


class UserInDB(UserBase):
    """User schema as stored in database (with hashed password)."""
    hashed_password: str 