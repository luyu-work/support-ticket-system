from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import get_application_settings

application_settings = get_application_settings()

_engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}
if application_settings.uses_sqlite_database:
    # SQLite needs this flag when used with FastAPI/threads
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
    }

database_engine = create_engine(
    application_settings.database_connection_url,
    **_engine_kwargs,
)

DatabaseSessionFactory = sessionmaker(
    bind=database_engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
)


class DatabaseModelBase(DeclarativeBase):
    """Base class for all SQLAlchemy models (User, Ticket, Comment, …)."""


def create_database_tables_if_needed() -> None:
    """
    For local SQLite only: create tables without Alembic/Docker.
    PostgreSQL still uses: python -m alembic upgrade head
    """
    if not application_settings.uses_sqlite_database:
        return

    # Import models so metadata knows all tables
    import app.models  # noqa: F401

    DatabaseModelBase.metadata.create_all(bind=database_engine)
    _sqlite_add_missing_agent_columns()


def _sqlite_add_missing_agent_columns() -> None:
    """create_all does not ALTER existing tables — add agent profile columns if missing."""
    from sqlalchemy import inspect, text

    inspector = inspect(database_engine)
    if "user_accounts" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("user_accounts")}
    alters: list[str] = []
    if "agent_number" not in existing:
        alters.append("ALTER TABLE user_accounts ADD COLUMN agent_number INTEGER")
    if "work_days" not in existing:
        alters.append("ALTER TABLE user_accounts ADD COLUMN work_days TEXT")
    if "work_time_start" not in existing:
        alters.append("ALTER TABLE user_accounts ADD COLUMN work_time_start VARCHAR(5)")
    if "work_time_end" not in existing:
        alters.append("ALTER TABLE user_accounts ADD COLUMN work_time_end VARCHAR(5)")
    if "admin_visible_password" not in existing:
        alters.append("ALTER TABLE user_accounts ADD COLUMN admin_visible_password VARCHAR(128)")
    if not alters:
        return
    with database_engine.begin() as connection:
        for statement in alters:
            connection.execute(text(statement))


def get_database_session() -> Generator[Session]:
    """
    FastAPI dependency: one DB session per request.
    Session closes automatically after the request finishes.
    """
    database_session = DatabaseSessionFactory()
    try:
        yield database_session
    finally:
        database_session.close()
