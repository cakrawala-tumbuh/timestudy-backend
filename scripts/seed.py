#!/usr/bin/env python
"""Seed script — create the first superadmin user and a default OAuth2 client."""
from __future__ import annotations

import sys
from pathlib import Path

# Make sure the app package is importable when running from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import secrets

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models.oauth import OAuthClient
from app.models.user import User
from app.services.auth_service import hash_password


def seed() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── Admin user ──────────────────────────────────────────────────────────
        if not db.query(User).filter(User.username == settings.FIRST_ADMIN_USERNAME).first():
            user = User(
                username=settings.FIRST_ADMIN_USERNAME,
                email=settings.FIRST_ADMIN_EMAIL,
                hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                is_active=True,
                is_superuser=True,
                full_name="System Administrator",
            )
            db.add(user)
            print(f"[seed] Created admin user: {settings.FIRST_ADMIN_USERNAME}")
        else:
            print(f"[seed] Admin user '{settings.FIRST_ADMIN_USERNAME}' already exists — skipped")

        # ── Default OAuth2 client ───────────────────────────────────────────────
        default_client_name = "TimeStudy Android"
        if not db.query(OAuthClient).filter(OAuthClient.client_name == default_client_name).first():
            client_id = secrets.token_urlsafe(24)
            client = OAuthClient(
                client_id=client_id,
                client_name=default_client_name,
                redirect_uris="com.example.timestudy://callback",
                scope="sync",
                grant_types="authorization_code refresh_token",
                response_types="code",
                description="Default client for the TimeStudy Android application",
                is_active=True,
            )
            db.add(client)
            print(f"[seed] Created OAuth2 client: {default_client_name}")
            print(f"[seed]   client_id = {client_id}")
        else:
            print(f"[seed] OAuth2 client '{default_client_name}' already exists — skipped")

        db.commit()
        print("[seed] Done.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
