from fastapi import APIRouter

from app.api.auth import auth_router
from app.api.health import health_router
from app.api.pages import pages_router

api_router = APIRouter()
api_router.include_router(pages_router)
api_router.include_router(health_router)
api_router.include_router(auth_router)
