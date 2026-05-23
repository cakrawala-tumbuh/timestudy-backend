"""Pydantic schemas for respondent CRUD operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RespondentBase(BaseModel):
    """Shared fields for creating and updating a respondent."""

    resp_id: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Z0-9\-]+$")
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    department: str | None = Field(default=None, max_length=100)
    position: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class RespondentCreate(RespondentBase):
    """Payload for creating a new respondent."""

    pin: str | None = Field(default=None, min_length=4, max_length=20)


class RespondentUpdate(BaseModel):
    """Payload for updating a respondent. All fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    department: str | None = Field(default=None, max_length=100)
    position: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    pin: str | None = Field(default=None, min_length=4, max_length=20)


class RespondentResponse(RespondentBase):
    """Respondent data returned from the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
