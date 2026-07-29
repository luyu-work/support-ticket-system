import logging

from fastapi import FastAPI

from app.api.router import api_router
from app.core.logging_setup import configure_application_logging
from app.core.settings import get_application_settings

logger = logging.getLogger(__name__)


def create_ticket_system_application() -> FastAPI:
    """Build and return the FastAPI application (factory)."""
    settings = get_application_settings()
    configure_application_logging(settings)

    ticket_system_application = FastAPI(
        title="Support Ticket System",
        description="Clients create tickets; agents work on them; admin watches the pool.",
        version="0.1.0",
        debug=settings.application_debug,
    )
    ticket_system_application.include_router(api_router)

    logger.info(
        "Ticket system API created | environment=%s",
        settings.application_environment,
    )
    return ticket_system_application


# ASGI entrypoint for uvicorn: app.main:ticket_system_application
ticket_system_application = create_ticket_system_application()
