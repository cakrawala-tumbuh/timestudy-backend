"""API router for daily log management (admin CRUD) and the Android sync endpoint."""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_respondent, get_current_user
from app.models.daily_log import DailyLog
from app.models.respondent import Respondent
from app.models.user import User
from app.schemas.common import PagedResponse
from app.schemas.daily_log import DailyLogCreate, DailyLogResponse, DailyLogUpdate

router = APIRouter(prefix="/daily-logs", tags=["Daily Logs"])


def _calculate_total_jam(jam_masuk: str, jam_pulang: str, menit_istirahat: int) -> float:
    """Calculate net working hours from attendance data."""
    h_m, min_m = map(int, jam_masuk.split(":"))
    h_p, min_p = map(int, jam_pulang.split(":"))
    total_minutes = (h_p * 60 + min_p) - (h_m * 60 + min_m) - menit_istirahat
    return round(max(total_minutes / 60, 0.0), 2)


def _apply_log_data(log: DailyLog, payload: DailyLogCreate | DailyLogUpdate) -> None:
    """Apply *payload* fields onto *log* and recompute derived fields."""
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(log, field, value)

    pct_sum = (
        log.pct_core
        + log.pct_copilot
        + log.pct_character
        + log.pct_improve
        + log.pct_strategic
        + log.pct_admin
        + log.pct_recovery
    )
    log.total_pct = round(pct_sum, 2)
    log.total_jam_hitung = _calculate_total_jam(log.jam_masuk, log.jam_pulang, log.menit_istirahat)


# ---------------------------------------------------------------------------
# Admin endpoints (portal)
# ---------------------------------------------------------------------------


@router.get("", response_model=PagedResponse[DailyLogResponse], summary="List daily logs (admin)")
def list_daily_logs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    resp_id: str | None = Query(default=None),
    tanggal_from: str | None = Query(default=None, description="yyyy-MM-dd"),
    tanggal_to: str | None = Query(default=None, description="yyyy-MM-dd"),
    is_synced: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PagedResponse[DailyLogResponse]:
    """Return a paginated list of daily logs with optional filters."""
    query = db.query(DailyLog)
    if resp_id:
        query = query.filter(DailyLog.resp_id == resp_id)
    if tanggal_from:
        query = query.filter(DailyLog.tanggal >= tanggal_from)
    if tanggal_to:
        query = query.filter(DailyLog.tanggal <= tanggal_to)
    if is_synced is not None:
        query = query.filter(DailyLog.is_synced == is_synced)
    query = query.order_by(DailyLog.tanggal.desc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return PagedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.get("/{log_id}", response_model=DailyLogResponse, summary="Get daily log (admin)")
def get_daily_log(
    log_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DailyLog:
    """Return a single daily log by ID."""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return log


@router.patch("/{log_id}", response_model=DailyLogResponse, summary="Update daily log (admin)")
def update_daily_log(
    log_id: int,
    payload: DailyLogUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DailyLog:
    """Partially update a daily log."""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    _apply_log_data(log, payload)
    db.commit()
    db.refresh(log)
    return log


@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete daily log (admin)",
)
def delete_daily_log(
    log_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    """Delete a daily log by ID."""
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    db.delete(log)
    db.commit()


# ---------------------------------------------------------------------------
# Respondent (Android app) endpoints — authenticated via OAuth2 token
# ---------------------------------------------------------------------------


@router.post(
    "/sync",
    response_model=DailyLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sync daily log (Android)",
)
def sync_daily_log(
    payload: DailyLogCreate,
    db: Session = Depends(get_db),
    current_respondent: Respondent = Depends(get_current_respondent),
) -> DailyLog:
    """Upsert a daily log submitted by the Android app."""
    if payload.resp_id != current_respondent.resp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot submit logs for another respondent",
        )

    existing = (
        db.query(DailyLog)
        .filter(
            DailyLog.resp_id == payload.resp_id,
            DailyLog.tanggal == payload.tanggal,
        )
        .first()
    )

    if existing:
        _apply_log_data(existing, payload)
        existing.is_synced = True
        db.commit()
        db.refresh(existing)
        return existing

    log = DailyLog(
        resp_id=payload.resp_id,
        tanggal=payload.tanggal,
        jam_masuk=payload.jam_masuk,
        jam_pulang=payload.jam_pulang,
        menit_istirahat=payload.menit_istirahat,
        day_color=payload.day_color,
        pct_core=payload.pct_core,
        pct_copilot=payload.pct_copilot,
        pct_character=payload.pct_character,
        pct_improve=payload.pct_improve,
        pct_strategic=payload.pct_strategic,
        pct_admin=payload.pct_admin,
        pct_recovery=payload.pct_recovery,
        notes=payload.notes,
        is_synced=True,
    )
    _apply_log_data(log, payload)
    log.is_synced = True
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
