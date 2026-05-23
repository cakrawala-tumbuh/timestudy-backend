"""FastAPI application factory for the TimeStudy backend API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import (
    auth_router,
    clients_router,
    daily_logs_router,
    oauth_router,
    respondents_router,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create database tables on startup (for development / first run)."""
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    """Application factory — construct and configure the FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "REST API for TimeStudy — manages respondents, daily work-time logs, "
            "and OAuth2 PKCE authentication for the Android app."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(respondents_router, prefix=api_prefix)
    app.include_router(daily_logs_router, prefix=api_prefix)
    app.include_router(clients_router, prefix=api_prefix)

    # OAuth2 endpoints at root level (as required by Android's AppAuth)
    app.include_router(oauth_router)

    @app.get("/health", tags=["Health"])
    def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()
