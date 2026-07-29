from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import get_application_settings

application_settings = get_application_settings()

_engine_kwargs: dict = {"pool_pre_ping": True}
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


def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency: one DB session per request.
    Session closes automatically after the request finishes.
    """
    database_session = DatabaseSessionFactory()
    try:
        yield database_session
    finally:
        database_session.close()
