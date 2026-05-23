"""Pydantic schemas for OAuth2 PKCE client management and token exchange."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OAuthClientBase(BaseModel):
    """Shared fields for creating and updating an OAuth2 client registration."""

    client_name: str = Field(..., min_length=1, max_length=100)
    redirect_uris: str = Field(..., description="Space-separated list of allowed redirect URIs")
    scope: str = Field(default="sync", description="Space-separated list of allowed scopes")
    grant_types: str = Field(default="authorization_code refresh_token")
    response_types: str = Field(default="code")
    description: str | None = None
    is_active: bool = True


class OAuthClientCreate(OAuthClientBase):
    """Payload for registering a new OAuth2 client."""


class OAuthClientUpdate(BaseModel):
    """Payload for updating an OAuth2 client. All fields optional."""

    client_name: str | None = Field(default=None, min_length=1, max_length=100)
    redirect_uris: str | None = None
    scope: str | None = None
    grant_types: str | None = None
    response_types: str | None = None
    description: str | None = None
    is_active: bool | None = None


class OAuthClientResponse(OAuthClientBase):
    """OAuth2 client data returned from the API."""

    id: str
    client_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """OAuth2 token response (RFC 6749 §5.1)."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str | None = None
    scope: str = "sync"


class AuthorizeRequest(BaseModel):
    """Query parameters for the OAuth2 authorization endpoint."""

    response_type: str = Field(default="code")
    client_id: str
    redirect_uri: str
    scope: str = "sync"
    state: str | None = None
    code_challenge: str = Field(..., description="PKCE code challenge (Base64URL SHA-256)")
    code_challenge_method: str = Field(default="S256")


class TokenRequest(BaseModel):
    """Form fields for the OAuth2 token endpoint."""

    grant_type: str
    code: str | None = None
    redirect_uri: str | None = None
    client_id: str | None = None
    code_verifier: str | None = None
    refresh_token: str | None = None
