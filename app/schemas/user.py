"""Pydantic schemas for admin user authentication and account management."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Shared fields for creating and updating an admin user account."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Payload for creating a new admin user."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Payload for updating an existing admin user."""

    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class UserResponse(UserBase):
    """Admin user data returned from the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Credentials for admin login."""

    username: str
    password: str


class Token(BaseModel):
    """JWT token pair returned on successful login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str
