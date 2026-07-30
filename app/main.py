import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.database import create_database_tables_if_needed
from app.core.logging_setup import configure_application_logging
from app.core.settings import get_application_settings
from app.services.seed_staff_accounts import seed_default_staff_accounts_on_startup

logger = logging.getLogger(__name__)

@asynccontextmanager
async def ticket_system_lifespan(_application: FastAPI):
    """При старте: при необходимости создаём таблицы SQLite и сидим админа/агента."""
    create_database_tables_if_needed()
    seed_default_staff_accounts_on_startup()
    yield

def create_ticket_system_application() -> FastAPI:
    """Собирает и возвращает приложение FastAPI."""
    settings = get_application_settings()
    configure_application_logging(settings)

    ticket_system_application = FastAPI(
        title="Support Ticket System",
        description=("Clients create tickets; agents work the pool; admin manages agents."),
        version="1.1.0",
        debug=settings.application_debug,
        lifespan=ticket_system_lifespan,
    )

    ticket_system_application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ticket_system_application.include_router(api_router)

    logger.info(
        "Ticket system API created | environment=%s | database=%s",
        settings.application_environment,
        "sqlite" if settings.uses_sqlite_database else "postgresql",
    )
    return ticket_system_application

ticket_system_application = create_ticket_system_application()
