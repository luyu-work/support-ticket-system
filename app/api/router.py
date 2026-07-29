from fastapi import APIRouter

from app.api.admin import admin_router
from app.api.auth import auth_router
from app.api.health import health_router
from app.api.tickets import tickets_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(tickets_router)
api_router.include_router(admin_router)
