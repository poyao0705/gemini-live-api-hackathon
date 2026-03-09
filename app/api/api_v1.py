"""API v1 router — assembles all endpoint routers."""

from fastapi import APIRouter

from app.api.endpoints import health, meetings, webhooks

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(webhooks.router)
api_router.include_router(meetings.router)
