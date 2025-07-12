"""Pydantic schemas for user models."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50, description="Username must be 3-50 characters")
    email: EmailStr | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserCreate(BaseModel):
    """Schema for user registration requests."""
    username: str = Field(..., min_length=3, max_length=50, description="Username must be 3-50 characters")
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100, description="Full name is required")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class User(UserBase):
    """User schema for responses (without password)."""
    pass


class UserInDB(UserBase):
    """User schema as stored in database (with hashed password)."""
    hashed_password: str
