"""Business logic for the OAuth2 PKCE authorization server: PKCE verification, code exchange, and token management."""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.oauth import OAuthAuthorizationCode, OAuthClient, OAuthToken
from app.models.respondent import Respondent
from app.schemas.oauth import TokenResponse

pin_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pin(pin: str) -> str:
    """Return bcrypt hash of a respondent PIN."""
    return pin_context.hash(pin)


def verify_pin(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed* PIN."""
    return pin_context.verify(plain, hashed)


def authenticate_respondent(db: Session, resp_id: str, pin: str) -> Respondent | None:
    """Return the Respondent if resp_id and PIN are valid, otherwise None."""
    resp = (
        db.query(Respondent)
        .filter(Respondent.resp_id == resp_id, Respondent.is_active == True)  # noqa: E712
        .first()
    )
    if not resp:
        return None
    if not resp.pin_hash:
        return None
    if not verify_pin(pin, resp.pin_hash):
        return None
    return resp


def verify_pkce_challenge(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    """Verify PKCE code_verifier against stored code_challenge (RFC 7636)."""
    if method != "S256":
        return False
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return computed == code_challenge


def create_authorization_code(
    db: Session,
    *,
    client_id: str,
    resp_id: str,
    redirect_uri: str,
    scope: str,
    code_challenge: str,
    code_challenge_method: str,
) -> OAuthAuthorizationCode:
    """Generate and persist a new authorization code."""
    settings = get_settings()
    code = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.OAUTH_CODE_EXPIRE_SECONDS
    )
    auth_code = OAuthAuthorizationCode(
        client_id=client_id,
        resp_id=resp_id,
        code=code,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        redirect_uri=redirect_uri,
        scope=scope,
        expires_at=expires_at,
    )
    db.add(auth_code)
    db.commit()
    db.refresh(auth_code)
    return auth_code


def exchange_code_for_token(
    db: Session,
    *,
    code: str,
    client_id: str,
    redirect_uri: str,
    code_verifier: str,
) -> TokenResponse | None:
    """Exchange an authorization code for an access/refresh token pair.

    Returns None if the code is invalid, expired, or the PKCE verifier is wrong.
    """
    auth_code = (
        db.query(OAuthAuthorizationCode)
        .filter(
            OAuthAuthorizationCode.code == code,
            OAuthAuthorizationCode.client_id == client_id,
        )
        .first()
    )
    if not auth_code:
        return None
    if auth_code.is_expired():
        db.delete(auth_code)
        db.commit()
        return None
    if auth_code.redirect_uri != redirect_uri:
        return None
    if not verify_pkce_challenge(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
        return None

    # All checks pass — issue token
    settings = get_settings()
    access_token = secrets.token_urlsafe(64)
    refresh_token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token = OAuthToken(
        client_id=client_id,
        resp_id=auth_code.resp_id,
        access_token=access_token,
        refresh_token=refresh_token,
        scope=auth_code.scope,
        expires_at=expires_at,
    )
    db.add(token)
    db.delete(auth_code)
    db.commit()
    db.refresh(token)

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        scope=token.scope,
    )


def refresh_access_token(
    db: Session,
    *,
    refresh_token: str,
    client_id: str,
) -> TokenResponse | None:
    """Issue a new access token given a valid refresh token."""
    token = (
        db.query(OAuthToken)
        .filter(
            OAuthToken.refresh_token == refresh_token,
            OAuthToken.client_id == client_id,
        )
        .first()
    )
    if not token or token.is_revoked():
        return None

    settings = get_settings()
    new_access = secrets.token_urlsafe(64)
    new_expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token.access_token = new_access
    token.expires_at = new_expires
    db.commit()
    db.refresh(token)

    return TokenResponse(
        access_token=new_access,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        scope=token.scope,
    )


def revoke_token(db: Session, *, token_value: str) -> bool:
    """Revoke an access or refresh token. Returns True if found."""
    token = (
        db.query(OAuthToken)
        .filter(
            (OAuthToken.access_token == token_value)
            | (OAuthToken.refresh_token == token_value)
        )
        .first()
    )
    if not token:
        return False
    token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def get_token_respondent(db: Session, access_token: str) -> Respondent | None:
    """Return the Respondent associated with *access_token*, or None if invalid."""
    token = (
        db.query(OAuthToken)
        .filter(OAuthToken.access_token == access_token)
        .first()
    )
    if not token or not token.is_active():
        return None
    return (
        db.query(Respondent)
        .filter(Respondent.resp_id == token.resp_id, Respondent.is_active == True)  # noqa: E712
        .first()
    )


def get_client_by_client_id(db: Session, client_id: str) -> OAuthClient | None:
    """Return the OAuthClient for *client_id* if it exists and is active."""
    return (
        db.query(OAuthClient)
        .filter(OAuthClient.client_id == client_id, OAuthClient.is_active == True)  # noqa: E712
        .first()
    )
