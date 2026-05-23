"""Pydantic schemas for daily work-time log creation, update, and API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DayColor = Literal["G", "Y", "R"]


class DailyLogBase(BaseModel):
    """Shared fields for creating and updating a daily log entry."""

    resp_id: str = Field(..., min_length=1, max_length=20)
    tanggal: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="yyyy-MM-dd")
    jam_masuk: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:mm")
    jam_pulang: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="HH:mm")
    menit_istirahat: int = Field(default=60, ge=0, le=480)
    day_color: DayColor = "G"
    pct_core: float = Field(default=0.0, ge=0.0, le=100.0)
    pct_copilot: float = Field(default=0.0, ge=0.0, le=100.0)
    pct_character: float = Field(default=0.0, ge=0.0, le=100.0)
    pct_improve: float = Field(default=0.0, ge=0.0, le=100.0)
    pct_strategic: float = Field(default=0.0, ge=0.0, le=100.0)
    pct_admin: float = Field(default=0.0, ge=0.0, le=100.0)
    pct_recovery: float = Field(default=0.0, ge=0.0, le=100.0)
    notes: str | None = None


class DailyLogCreate(DailyLogBase):
    """Payload for creating or upserting a daily log (submitted by Android app)."""

    @model_validator(mode="after")
    def validate_total_pct(self) -> DailyLogCreate:
        """Validate that the sum of all seven time-category percentages does not exceed 110%."""
        total = (
            self.pct_core
            + self.pct_copilot
            + self.pct_character
            + self.pct_improve
            + self.pct_strategic
            + self.pct_admin
            + self.pct_recovery
        )
        if total > 110.0:
            raise ValueError(f"Sum of percentages ({total:.1f}) must not exceed 110%")
        return self


class DailyLogUpdate(BaseModel):
    """Payload for partial update of a daily log."""

    jam_masuk: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    jam_pulang: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    menit_istirahat: int | None = Field(default=None, ge=0, le=480)
    day_color: DayColor | None = None
    pct_core: float | None = Field(default=None, ge=0.0, le=100.0)
    pct_copilot: float | None = Field(default=None, ge=0.0, le=100.0)
    pct_character: float | None = Field(default=None, ge=0.0, le=100.0)
    pct_improve: float | None = Field(default=None, ge=0.0, le=100.0)
    pct_strategic: float | None = Field(default=None, ge=0.0, le=100.0)
    pct_admin: float | None = Field(default=None, ge=0.0, le=100.0)
    pct_recovery: float | None = Field(default=None, ge=0.0, le=100.0)
    notes: str | None = None


class DailyLogResponse(DailyLogBase):
    """Daily log data returned from the API."""

    id: int
    total_jam_hitung: float | None
    total_pct: float
    is_synced: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
