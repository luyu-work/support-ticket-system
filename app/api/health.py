from fastapi import APIRouter

from app.core.settings import get_application_settings

health_router = APIRouter(tags=["health"])

@health_router.get("/health")
def check_application_health() -> dict[str, str]:
    """Простая проверка: приложение живо и отвечает."""
    settings = get_application_settings()
    return {
        "status": "ok",
        "application_name": settings.application_name,
        "application_environment": settings.application_environment,
    }
