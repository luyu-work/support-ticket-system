from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import get_application_settings

application_settings = get_application_settings()

database_engine = create_engine(
    application_settings.database_connection_url,
    pool_pre_ping=True,
)

DatabaseSessionFactory = sessionmaker(
    bind=database_engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
)


class DatabaseModelBase(DeclarativeBase):
    """Base class for all SQLAlchemy models (User, Ticket, Comment, …)."""


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
