"""SQLAlchemy ORM model for survey respondents (one entry per Android device user)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Respondent(Base):
    """Survey respondent — one entry per Android device user."""

    __tablename__ = "respondents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resp_id: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False, comment="e.g. R-001"
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pin_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Hashed PIN for OAuth2 login"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    daily_logs: Mapped[list["DailyLog"]] = relationship(  # noqa: F821
        "DailyLog", back_populates="respondent", cascade="all, delete-orphan"
    )
