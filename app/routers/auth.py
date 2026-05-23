"""API router for admin authentication: login, token refresh, and current-user endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_superuser, get_current_user
from app.models.user import User
from app.schemas.user import RefreshTokenRequest, Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import (
    authenticate_user,
    build_token_pair,
    create_access_token,
    decode_token,
    get_user_from_token,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token, summary="Admin login")
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Authenticate an admin user and return a JWT token pair."""
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return build_token_pair(user.id)


@router.post("/refresh", response_model=Token, summary="Refresh access token")
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> Token:
    """Exchange a refresh token for a new access token pair."""
    from jose import JWTError

    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )
        user_id = int(data["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    return build_token_pair(user.id)


@router.get("/me", response_model=UserResponse, summary="Get current admin user")
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated admin user."""
    return current_user


@router.post("/users", response_model=UserResponse, summary="Create admin user")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> User:
    """Create a new admin user. Requires superuser privilege."""
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )
    user = User(
        username=payload.username,
        email=str(payload.email),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=payload.is_active,
        is_superuser=payload.is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
