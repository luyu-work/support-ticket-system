"""Unit tests for admin schema validators."""

import pytest
from pydantic import ValidationError

from app.schemas.admin import (
    AgentCreateRequest,
    validate_hh_mm,
    validate_work_days,
)


def test_validate_work_days_dedupe_and_sort() -> None:
    assert validate_work_days([4, 0, 0, 2]) == [0, 2, 4]


def test_validate_work_days_empty() -> None:
    with pytest.raises(ValueError):
        validate_work_days([])


def test_validate_hh_mm() -> None:
    assert validate_hh_mm("9:5") == "09:05"
    with pytest.raises(ValueError):
        validate_hh_mm("25:00")


def test_agent_create_request_accepts_valid_payload() -> None:
    body = AgentCreateRequest(
        full_name="Test Agent",
        agent_number=3,
        email="a3@example.com",
        password="pass1234",
        work_days=[0, 1, 2],
        work_time_start="09:00",
        work_time_end="18:00",
    )
    assert body.email == "a3@example.com"
    assert body.work_time_start == "09:00"


def test_agent_create_request_normalizes_email() -> None:
    body = AgentCreateRequest(
        full_name="Test Agent",
        agent_number=4,
        email="  Agent@Example.com ",
        password="pass1234",
        work_days=[0],
        work_time_start="09:00",
        work_time_end="18:00",
    )
    assert body.email == "agent@example.com"


def test_agent_create_request_rejects_bad_email() -> None:
    with pytest.raises(ValidationError):
        AgentCreateRequest(
            full_name="Test Agent",
            agent_number=3,
            email="not-an-email",
            password="pass1234",
            work_days=[0],
            work_time_start="09:00",
            work_time_end="18:00",
        )


def test_agent_create_request_rejects_bad_time() -> None:
    with pytest.raises(ValidationError):
        AgentCreateRequest(
            full_name="Test Agent",
            agent_number=3,
            email="a3@example.com",
            password="pass1234",
            work_days=[0],
            work_time_start="99:00",
            work_time_end="18:00",
        )
