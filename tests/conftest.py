"""
Shared pytest fixtures.

Tests use an in-memory SQLite DB so they run without Docker/PostgreSQL.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import get_database_session
from app.main import ticket_system_application
from app.models import DatabaseModelBase


@pytest.fixture(autouse=True)
def _reset_ticket_service_cooldowns() -> None:
    """Isolate process-wide cooldowns between tests."""
    from app.services.support_ticket_service import reset_promote_cooldown_for_tests

    reset_promote_cooldown_for_tests()
    yield


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


@pytest.fixture()
def api_test_client(database_session: Session) -> TestClient:
    """HTTP client with the same in-memory DB as database_session."""

    def override_get_database_session():
        try:
            yield database_session
        finally:
            pass

    ticket_system_application.dependency_overrides[get_database_session] = (
        override_get_database_session
    )
    with TestClient(ticket_system_application) as test_client:
        yield test_client
    ticket_system_application.dependency_overrides.clear()
