"""SQLAlchemy ORM model for daily work-time logs submitted by respondents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

DayColorLiteral = Literal["G", "Y", "R"]


class DailyLog(Base):
    """Daily work time log submitted by a respondent."""

    __tablename__ = "daily_logs"
    __table_args__ = (
        UniqueConstraint("resp_id", "tanggal", name="uq_daily_log_resp_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    resp_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("respondents.resp_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tanggal: Mapped[str] = mapped_column(String(10), nullable=False, comment="yyyy-MM-dd")
    jam_masuk: Mapped[str] = mapped_column(String(5), nullable=False, comment="HH:mm")
    jam_pulang: Mapped[str] = mapped_column(String(5), nullable=False, comment="HH:mm")
    menit_istirahat: Mapped[int] = mapped_column(Integer, default=60)
    total_jam_hitung: Mapped[float | None] = mapped_column(Float, nullable=True)
    day_color: Mapped[str] = mapped_column(
        String(1), default="G", comment="G=Normal, Y=Busy, R=Peak"
    )

    # 7 time allocation percentages
    pct_core: Mapped[float] = mapped_column(Float, default=0.0)
    pct_copilot: Mapped[float] = mapped_column(Float, default=0.0)
    pct_character: Mapped[float] = mapped_column(Float, default=0.0)
    pct_improve: Mapped[float] = mapped_column(Float, default=0.0)
    pct_strategic: Mapped[float] = mapped_column(Float, default=0.0)
    pct_admin: Mapped[float] = mapped_column(Float, default=0.0)
    pct_recovery: Mapped[float] = mapped_column(Float, default=0.0)
    total_pct: Mapped[float] = mapped_column(Float, default=0.0)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    respondent: Mapped["Respondent"] = relationship(  # noqa: F821
        "Respondent", back_populates="daily_logs"
    )
