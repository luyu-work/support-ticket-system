from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.database import DatabaseModelBase
from app.core.settings import get_application_settings

# Register all models on metadata so Alembic can autogenerate later
from app.models import (  # noqa: F401
    SupportTicket,
    TicketAttachment,
    TicketComment,
    UserAccount,
)

alembic_config = context.config
application_settings = get_application_settings()

alembic_config.set_main_option(
    "sqlalchemy.url",
    application_settings.database_connection_url,
)

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

target_metadata = DatabaseModelBase.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (SQL script mode)."""
    database_url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database."""
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
