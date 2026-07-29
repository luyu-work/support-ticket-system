"""
Shared pytest fixtures.

Tests use an in-memory SQLite DB so they run without Docker/PostgreSQL.
"""

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import DatabaseModelBase


@pytest.fixture()
def database_session() -> Session:
    """Fresh empty DB for each test, closed afterwards."""
    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    DatabaseModelBase.metadata.create_all(bind=test_engine)
    TestSessionFactory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    session = TestSessionFactory()
    try:
        yield session
    finally:
        session.close()
        DatabaseModelBase.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
