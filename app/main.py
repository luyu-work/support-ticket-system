import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.database import create_database_tables_if_needed
from app.core.logging_setup import configure_application_logging
from app.core.settings import get_application_settings
from app.services.seed_staff_accounts import seed_default_staff_accounts_on_startup

logger = logging.getLogger(__name__)

WEB_STATIC_DIRECTORY = Path(__file__).resolve().parent / "web" / "static"


@asynccontextmanager
async def ticket_system_lifespan(_application: FastAPI):
    """On startup: create SQLite tables if needed, then seed admin/agent."""
    create_database_tables_if_needed()
    seed_default_staff_accounts_on_startup()
    yield


def create_ticket_system_application() -> FastAPI:
    """Build and return the FastAPI application (factory)."""
    settings = get_application_settings()
    configure_application_logging(settings)

    ticket_system_application = FastAPI(
        title="Support Ticket System",
        description="Clients create tickets; agents work on them; admin watches the pool.",
        version="0.5.0",
        debug=settings.application_debug,
        lifespan=ticket_system_lifespan,
    )
    ticket_system_application.mount(
        "/static",
        StaticFiles(directory=str(WEB_STATIC_DIRECTORY)),
        name="static",
    )
    ticket_system_application.include_router(api_router)

    logger.info(
        "Ticket system API created | environment=%s | database=%s",
        settings.application_environment,
        "sqlite" if settings.uses_sqlite_database else "postgresql",
    )
    return ticket_system_application


# ASGI entrypoint for uvicorn: app.main:ticket_system_application
ticket_system_application = create_ticket_system_application()
