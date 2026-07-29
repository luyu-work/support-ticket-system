"""Admin CRUD for support agents."""

from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_plain_password
from app.models import UserAccount, UserRole
from app.schemas.admin import WEEKDAY_LABELS_RU
from app.services.support_ticket_service import format_agent_badge

logger = logging.getLogger(__name__)


class AgentNotFoundError(Exception):
    pass


class AgentNumberTakenError(Exception):
    pass


class AgentEmailTakenError(Exception):
    pass


class AgentValidationError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def parse_work_days(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return sorted({int(day) for day in data if 0 <= int(day) <= 6})
    except (TypeError, ValueError, json.JSONDecodeError):
        pass
    return []


def dump_work_days(days: list[int]) -> str:
    return json.dumps(sorted({day for day in days if 0 <= day <= 6}))


def work_days_label(days: list[int]) -> str:
    if not days:
        return "—"
    if days == [0, 1, 2, 3, 4]:
        return "Пн–Пт"
    if days == [0, 1, 2, 3, 4, 5, 6]:
        return "Ежедневно"
    if days == [5, 6]:
        return "Сб–Вс"
    labels = [WEEKDAY_LABELS_RU[day] for day in days]
    return ", ".join(labels)


def work_time_label(start: str | None, end: str | None) -> str:
    if not start or not end:
        return "—"
    return f"{start}–{end}"


def _assert_time_range(start: str, end: str) -> None:
    def to_minutes(value: str) -> int:
        hour, minute = value.split(":")
        return int(hour) * 60 + int(minute)

    if to_minutes(start) >= to_minutes(end):
        raise AgentValidationError("Время окончания должно быть позже начала")


def agent_to_response(agent: UserAccount) -> dict:
    days = parse_work_days(agent.work_days)
    number = agent.agent_number
    return {
        "user_account_id": agent.user_account_id,
        "email": agent.email,
        "full_name": agent.full_name,
        "agent_number": number,
        "agent_badge": format_agent_badge(
            agent.user_account_id,
            agent_number=number,
        ),
        "is_active": agent.is_active,
        "is_online": agent.is_online,
        "work_days": days,
        "work_days_label": work_days_label(days),
        "work_time_start": agent.work_time_start,
        "work_time_end": agent.work_time_end,
        "work_time_label": work_time_label(agent.work_time_start, agent.work_time_end),
        "password": agent.admin_visible_password,
        "created_at": agent.created_at,
    }


def list_agents(database_session: Session, *, include_inactive: bool = False) -> list[UserAccount]:
    query = select(UserAccount).where(UserAccount.role == UserRole.AGENT)
    if not include_inactive:
        query = query.where(UserAccount.is_active.is_(True))
    query = query.order_by(
        UserAccount.agent_number.is_(None).asc(),
        UserAccount.agent_number.asc(),
        UserAccount.user_account_id.asc(),
    )
    return list(database_session.scalars(query).all())


def get_agent_by_id(database_session: Session, user_account_id: int) -> UserAccount | None:
    agent = database_session.get(UserAccount, user_account_id)
    if agent is None or agent.role != UserRole.AGENT:
        return None
    return agent


def _ensure_agent_number_free(
    database_session: Session,
    agent_number: int,
    *,
    exclude_user_id: int | None = None,
) -> None:
    existing = database_session.scalar(
        select(UserAccount).where(UserAccount.agent_number == agent_number)
    )
    if existing is None:
        return
    if exclude_user_id is not None and existing.user_account_id == exclude_user_id:
        return
    raise AgentNumberTakenError


def _ensure_email_free(
    database_session: Session,
    email: str,
    *,
    exclude_user_id: int | None = None,
) -> None:
    existing = database_session.scalar(
        select(UserAccount).where(UserAccount.email == email)
    )
    if existing is None:
        return
    if exclude_user_id is not None and existing.user_account_id == exclude_user_id:
        return
    raise AgentEmailTakenError


def create_agent(
    database_session: Session,
    *,
    full_name: str,
    agent_number: int,
    email: str,
    plain_password: str,
    work_days: list[int],
    work_time_start: str,
    work_time_end: str,
) -> UserAccount:
    _assert_time_range(work_time_start, work_time_end)
    _ensure_agent_number_free(database_session, agent_number)
    normalized_email = email.strip().lower()
    _ensure_email_free(database_session, normalized_email)

    agent = UserAccount(
        email=normalized_email,
        full_name=full_name.strip(),
        hashed_password=hash_plain_password(plain_password),
        admin_visible_password=plain_password,
        role=UserRole.AGENT,
        is_active=True,
        is_online=False,
        agent_number=agent_number,
        work_days=dump_work_days(work_days),
        work_time_start=work_time_start,
        work_time_end=work_time_end,
    )
    database_session.add(agent)
    database_session.commit()
    database_session.refresh(agent)
    logger.info("Agent created | id=%s number=%s", agent.user_account_id, agent_number)
    return agent


def update_agent(
    database_session: Session,
    *,
    user_account_id: int,
    full_name: str | None = None,
    agent_number: int | None = None,
    email: str | None = None,
    plain_password: str | None = None,
    work_days: list[int] | None = None,
    work_time_start: str | None = None,
    work_time_end: str | None = None,
) -> UserAccount:
    agent = get_agent_by_id(database_session, user_account_id)
    if agent is None or not agent.is_active:
        raise AgentNotFoundError

    if agent_number is not None:
        _ensure_agent_number_free(
            database_session,
            agent_number,
            exclude_user_id=agent.user_account_id,
        )
        agent.agent_number = agent_number

    if email is not None:
        normalized_email = email.strip().lower()
        _ensure_email_free(
            database_session,
            normalized_email,
            exclude_user_id=agent.user_account_id,
        )
        agent.email = normalized_email

    if full_name is not None:
        agent.full_name = full_name.strip()
    if plain_password:
        agent.hashed_password = hash_plain_password(plain_password)
        agent.admin_visible_password = plain_password
    if work_days is not None:
        agent.work_days = dump_work_days(work_days)

    start = work_time_start if work_time_start is not None else agent.work_time_start
    end = work_time_end if work_time_end is not None else agent.work_time_end
    if start and end:
        _assert_time_range(start, end)
    if work_time_start is not None:
        agent.work_time_start = work_time_start
    if work_time_end is not None:
        agent.work_time_end = work_time_end

    database_session.commit()
    database_session.refresh(agent)
    logger.info("Agent updated | id=%s", agent.user_account_id)
    return agent


def delete_agent(database_session: Session, *, user_account_id: int) -> None:
    """Soft-delete: deactivate agent (tickets history stays)."""
    agent = get_agent_by_id(database_session, user_account_id)
    if agent is None or not agent.is_active:
        raise AgentNotFoundError
    agent.is_active = False
    agent.is_online = False
    database_session.commit()
    logger.info("Agent deactivated | id=%s", user_account_id)
