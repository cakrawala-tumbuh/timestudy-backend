"""API router for respondent management — admin-only CRUD operations."""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.respondent import Respondent
from app.models.user import User
from app.schemas.common import PagedResponse
from app.schemas.respondent import RespondentCreate, RespondentResponse, RespondentUpdate
from app.services.oauth_service import hash_pin

router = APIRouter(prefix="/respondents", tags=["Respondents"])


@router.get("", response_model=PagedResponse[RespondentResponse], summary="List respondents")
def list_respondents(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, description="Search by resp_id or name"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PagedResponse[RespondentResponse]:
    """Return a paginated list of respondents."""
    query = db.query(Respondent)
    if search:
        pattern = f"%{search}%"
        query = query.filter(Respondent.resp_id.ilike(pattern) | Respondent.name.ilike(pattern))
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return PagedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post(
    "",
    response_model=RespondentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create respondent",
)
def create_respondent(
    payload: RespondentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Respondent:
    """Create a new respondent. *resp_id* must be unique."""
    if db.query(Respondent).filter(Respondent.resp_id == payload.resp_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Respondent '{payload.resp_id}' already exists",
        )
    resp = Respondent(
        resp_id=payload.resp_id,
        name=payload.name,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        department=payload.department,
        position=payload.position,
        is_active=payload.is_active,
        pin_hash=hash_pin(payload.pin) if payload.pin else None,
    )
    db.add(resp)
    db.commit()
    db.refresh(resp)
    return resp


@router.get("/{resp_id}", response_model=RespondentResponse, summary="Get respondent")
def get_respondent(
    resp_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Respondent:
    """Return a single respondent by *resp_id*."""
    resp = db.query(Respondent).filter(Respondent.resp_id == resp_id).first()
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Respondent not found")
    return resp


@router.patch("/{resp_id}", response_model=RespondentResponse, summary="Update respondent")
def update_respondent(
    resp_id: str,
    payload: RespondentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Respondent:
    """Partially update a respondent."""
    resp = db.query(Respondent).filter(Respondent.resp_id == resp_id).first()
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Respondent not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "pin" in update_data:
        pin = update_data.pop("pin")
        resp.pin_hash = hash_pin(pin) if pin else None
    if "email" in update_data and update_data["email"]:
        update_data["email"] = str(update_data["email"])

    for field, value in update_data.items():
        setattr(resp, field, value)

    db.commit()
    db.refresh(resp)
    return resp


@router.delete(
    "/{resp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete respondent",
)
def delete_respondent(
    resp_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    """Delete a respondent and all associated daily logs."""
    resp = db.query(Respondent).filter(Respondent.resp_id == resp_id).first()
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Respondent not found")
    db.delete(resp)
    db.commit()
