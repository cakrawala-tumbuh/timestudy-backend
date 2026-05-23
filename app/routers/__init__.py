"""Routers package."""

from app.routers.auth import router as auth_router
from app.routers.daily_logs import router as daily_logs_router
from app.routers.oauth import clients_router, router as oauth_router
from app.routers.respondents import router as respondents_router

__all__ = [
    "auth_router",
    "respondents_router",
    "daily_logs_router",
    "oauth_router",
    "clients_router",
]
