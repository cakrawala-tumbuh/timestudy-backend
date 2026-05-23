"""API router implementing the OAuth2 PKCE authorization server and OAuth2 client registry."""

from __future__ import annotations

import math
import secrets

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.oauth import OAuthClient
from app.models.user import User
from app.schemas.common import PagedResponse
from app.schemas.oauth import OAuthClientCreate, OAuthClientResponse, OAuthClientUpdate, TokenResponse
from app.services.oauth_service import (
    authenticate_respondent,
    create_authorization_code,
    exchange_code_for_token,
    get_client_by_client_id,
    refresh_access_token,
    revoke_token,
)

router = APIRouter(tags=["OAuth2"])

# ---------------------------------------------------------------------------
# OAuth2 Authorization Server endpoints (used by Android app)
# ---------------------------------------------------------------------------

AUTHORIZE_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TimeStudy — Otorisasi</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, sans-serif; background: #f0f4f8; display: flex;
            justify-content: center; align-items: center; min-height: 100vh; }}
    .card {{ background: white; border-radius: 12px; padding: 2rem; width: 100%;
             max-width: 380px; box-shadow: 0 4px 24px rgba(0,0,0,.08); }}
    h1 {{ font-size: 1.3rem; font-weight: 700; color: #1e3a5f; margin-bottom: .25rem; }}
    p.sub {{ font-size: .875rem; color: #64748b; margin-bottom: 1.5rem; }}
    .app-badge {{ background: #eff6ff; color: #1d4ed8; border-radius: 6px;
                  padding: .25rem .75rem; font-size: .8rem; font-weight: 600;
                  display: inline-block; margin-bottom: 1rem; }}
    label {{ display: block; font-size: .875rem; font-weight: 500; color: #374151;
             margin-bottom: .25rem; }}
    input {{ width: 100%; border: 1px solid #d1d5db; border-radius: 8px; padding: .6rem .75rem;
             font-size: .875rem; outline: none; transition: border-color .15s; }}
    input:focus {{ border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,.15); }}
    .group {{ margin-bottom: 1rem; }}
    .error {{ background: #fef2f2; color: #dc2626; border-radius: 6px; padding: .5rem .75rem;
              font-size: .8rem; margin-bottom: 1rem; }}
    button {{ width: 100%; background: #1d4ed8; color: white; border: none; border-radius: 8px;
              padding: .75rem; font-size: .9rem; font-weight: 600; cursor: pointer; }}
    button:hover {{ background: #1e40af; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="app-badge">{client_name}</div>
    <h1>Masuk ke TimeStudy</h1>
    <p class="sub">Masukkan kode responden dan PIN Anda.</p>
    {error_block}
    <form method="post">
      <input type="hidden" name="client_id" value="{client_id}">
      <input type="hidden" name="redirect_uri" value="{redirect_uri}">
      <input type="hidden" name="scope" value="{scope}">
      <input type="hidden" name="state" value="{state}">
      <input type="hidden" name="code_challenge" value="{code_challenge}">
      <input type="hidden" name="code_challenge_method" value="{code_challenge_method}">
      <div class="group">
        <label for="resp_id">Kode Responden</label>
        <input id="resp_id" name="resp_id" type="text" placeholder="Contoh: R-001" autocomplete="username">
      </div>
      <div class="group">
        <label for="pin">PIN</label>
        <input id="pin" name="pin" type="password" placeholder="PIN Anda" autocomplete="current-password">
      </div>
      <button type="submit">Masuk &amp; Otorisasi</button>
    </form>
  </div>
</body>
</html>
"""


@router.get("/oauth/authorize", response_class=HTMLResponse, response_model=None, include_in_schema=False)
def authorize_get(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(default="sync"),
    state: str = Query(default=""),
    code_challenge: str = Query(...),
    code_challenge_method: str = Query(default="S256"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Show the authorization login page (OAuth2 PKCE — GET)."""
    client = get_client_by_client_id(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown client")
    if not client.check_redirect_uri(redirect_uri):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="redirect_uri not registered"
        )
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported response_type"
        )
    if code_challenge_method != "S256":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only S256 code_challenge_method supported"
        )

    html = AUTHORIZE_HTML.format(
        client_name=client.client_name,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        error_block="",
    )
    return HTMLResponse(html)


@router.post("/oauth/authorize", response_class=HTMLResponse, response_model=None, include_in_schema=False)
def authorize_post(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(default="sync"),
    state: str = Form(default=""),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form(default="S256"),
    resp_id: str = Form(...),
    pin: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse | RedirectResponse:
    """Process the authorization form submission (OAuth2 PKCE — POST)."""
    client = get_client_by_client_id(db, client_id)
    if not client or not client.check_redirect_uri(redirect_uri):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    respondent = authenticate_respondent(db, resp_id, pin)
    if not respondent:
        error_block = '<div class="error">Kode responden atau PIN tidak valid.</div>'
        html = AUTHORIZE_HTML.format(
            client_name=client.client_name,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            error_block=error_block,
        )
        return HTMLResponse(html, status_code=200)

    auth_code = create_authorization_code(
        db,
        client_id=client_id,
        resp_id=respondent.resp_id,
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )

    callback = f"{redirect_uri}?code={auth_code.code}"
    if state:
        callback += f"&state={state}"
    return RedirectResponse(url=callback, status_code=status.HTTP_302_FOUND)


@router.post(
    "/oauth/token",
    response_model=TokenResponse,
    summary="OAuth2 Token endpoint",
    description=(
        "Exchange an authorization code for tokens (grant_type=authorization_code) "
        "or refresh an access token (grant_type=refresh_token). "
        "Supports PKCE (RFC 7636)."
    ),
)
def token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    code: str | None = Form(default=None),
    redirect_uri: str | None = Form(default=None),
    code_verifier: str | None = Form(default=None),
    refresh_token: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Issue an OAuth2 access/refresh token pair."""
    client = get_client_by_client_id(db, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client_id"
        )

    if grant_type == "authorization_code":
        if not code or not redirect_uri or not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code, redirect_uri and code_verifier are required",
            )
        result = exchange_code_for_token(
            db,
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid, expired or already used authorization code",
            )
        return result

    if grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_token is required"
            )
        result = refresh_access_token(db, refresh_token=refresh_token, client_id=client_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or revoked refresh token",
            )
        return result

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported grant_type: {grant_type}",
    )


@router.post(
    "/oauth/revoke",
    status_code=status.HTTP_200_OK,
    summary="Revoke OAuth2 token",
)
def revoke(
    token: str = Form(...),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke an access or refresh token (RFC 7009)."""
    revoke_token(db, token_value=token)
    return {"detail": "Token revoked"}


# ---------------------------------------------------------------------------
# Admin: OAuth2 Client management
# ---------------------------------------------------------------------------

clients_router = APIRouter(prefix="/oauth/clients", tags=["OAuth2 Clients"])


@clients_router.get(
    "", response_model=PagedResponse[OAuthClientResponse], summary="List OAuth2 clients"
)
def list_clients(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PagedResponse[OAuthClientResponse]:
    """Return a paginated list of registered OAuth2 clients."""
    query = db.query(OAuthClient)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return PagedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@clients_router.post(
    "",
    response_model=OAuthClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register OAuth2 client",
)
def create_client(
    payload: OAuthClientCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OAuthClient:
    """Register a new OAuth2 client application."""
    client_id = secrets.token_urlsafe(24)
    client = OAuthClient(
        client_id=client_id,
        client_name=payload.client_name,
        redirect_uris=payload.redirect_uris,
        scope=payload.scope,
        grant_types=payload.grant_types,
        response_types=payload.response_types,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@clients_router.get(
    "/{client_id}", response_model=OAuthClientResponse, summary="Get OAuth2 client"
)
def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OAuthClient:
    """Return a single OAuth2 client by *client_id*."""
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@clients_router.patch(
    "/{client_id}", response_model=OAuthClientResponse, summary="Update OAuth2 client"
)
def update_client(
    client_id: str,
    payload: OAuthClientUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OAuthClient:
    """Partially update an OAuth2 client."""
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@clients_router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete OAuth2 client",
)
def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    """Delete an OAuth2 client registration."""
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    db.delete(client)
    db.commit()
