"""Создаёт в БД дефолтных админа и агента."""

import logging

from sqlalchemy.orm import Session

from app.core.database import DatabaseSessionFactory
from app.core.settings import ApplicationSettings, get_application_settings
from app.models import UserRole
from app.services.user_account_service import ensure_staff_user_account

logger = logging.getLogger(__name__)

def seed_default_staff_accounts(
    database_session: Session,
    settings: ApplicationSettings | None = None,
) -> None:
    """Добавляет админа и агента, если их ещё нет в БД."""
    application_settings = settings or get_application_settings()

    admin_account = ensure_staff_user_account(
        database_session,
        email=application_settings.seed_admin_email,
        full_name=application_settings.seed_admin_full_name,
        plain_password=application_settings.seed_admin_password,
        role=UserRole.ADMIN,
    )
    agent_account = ensure_staff_user_account(
        database_session,
        email=application_settings.seed_agent_email,
        full_name=application_settings.seed_agent_full_name,
        plain_password=application_settings.seed_agent_password,
        role=UserRole.AGENT,
        agent_number=1,
        work_days="[0,1,2,3,4]",
        work_time_start="09:00",
        work_time_end="18:00",
    )

    logger.info(
        "Staff accounts ready | admin_id=%s agent_id=%s",
        admin_account.user_account_id,
        agent_account.user_account_id,
    )

def seed_default_staff_accounts_on_startup() -> None:
    """
    Открывает сессию БД и сидит сотрудников.
    Можно звать при старте API; если БД ещё не готова — пишем warning.
    """
    application_settings = get_application_settings()
    if not application_settings.seed_staff_on_startup:
        logger.info("Staff seed skipped (SEED_STAFF_ON_STARTUP=false)")
        return

    try:
        with DatabaseSessionFactory() as database_session:
            seed_default_staff_accounts(database_session, application_settings)
    except Exception as error:
        logger.warning(
            "Staff seed skipped — database not ready or seed failed: %s",
            error,
        )
