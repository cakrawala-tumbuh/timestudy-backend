"""SQLAlchemy ORM models for the OAuth2 PKCE authorization server (clients, codes, tokens)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OAuthClient(Base):
    """Registered OAuth2 client application (e.g., the Android app)."""

    __tablename__ = "oauth_clients"

    id: Mapped[str] = mapped_column(
        String(48),
        primary_key=True,
        default=lambda: secrets.token_urlsafe(32),
    )
    client_id: Mapped[str] = mapped_column(
        String(48), unique=True, index=True, nullable=False
    )
    client_name: Mapped[str] = mapped_column(String(100), nullable=False)
    client_secret: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        comment="NULL for public/PKCE clients",
    )
    # Space-separated list of allowed redirect URIs
    redirect_uris: Mapped[str] = mapped_column(Text, nullable=False)
    # Space-separated list of allowed scopes
    scope: Mapped[str] = mapped_column(Text, nullable=False, default="sync")
    # Space-separated grant types
    grant_types: Mapped[str] = mapped_column(
        Text, nullable=False, default="authorization_code refresh_token"
    )
    # Space-separated response types
    response_types: Mapped[str] = mapped_column(Text, nullable=False, default="code")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def check_redirect_uri(self, redirect_uri: str) -> bool:
        """Return True if *redirect_uri* is registered for this client."""
        return redirect_uri in self.redirect_uris.split()

    def check_grant_type(self, grant_type: str) -> bool:
        """Return True if *grant_type* is allowed for this client."""
        return grant_type in self.grant_types.split()

    def check_response_type(self, response_type: str) -> bool:
        """Return True if *response_type* is allowed for this client."""
        return response_type in self.response_types.split()


class OAuthAuthorizationCode(Base):
    """Short-lived authorization code issued during the OAuth2 PKCE flow."""

    __tablename__ = "oauth_authorization_codes"

    id: Mapped[str] = mapped_column(
        String(48),
        primary_key=True,
        default=lambda: secrets.token_urlsafe(32),
    )
    client_id: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    resp_id: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Authenticated respondent"
    )
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    # PKCE fields (RFC 7636)
    code_challenge: Mapped[str] = mapped_column(String(128), nullable=False)
    code_challenge_method: Mapped[str] = mapped_column(
        String(10), nullable=False, default="S256"
    )
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False, default="sync")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def is_expired(self) -> bool:
        """Return True if this authorization code has expired."""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)


class OAuthToken(Base):
    """Issued OAuth2 access/refresh token pair."""

    __tablename__ = "oauth_tokens"

    id: Mapped[str] = mapped_column(
        String(48),
        primary_key=True,
        default=lambda: secrets.token_urlsafe(32),
    )
    client_id: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    resp_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    access_token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    refresh_token: Mapped[str | None] = mapped_column(String(512), unique=True, nullable=True)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False, default="Bearer")
    scope: Mapped[str] = mapped_column(Text, nullable=False, default="sync")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def is_expired(self) -> bool:
        """Return True if this access token has expired."""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)

    def is_revoked(self) -> bool:
        """Return True if this token has been explicitly revoked."""
        return self.revoked_at is not None

    def is_active(self) -> bool:
        """Return True if the token is valid (not expired and not revoked)."""
        return not self.is_expired() and not self.is_revoked()
