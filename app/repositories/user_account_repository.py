"""Работа с БД: аккаунты клиентов, агентов, админов."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserAccount, UserRole

def get_user_account_by_id(
    database_session: Session,
    user_account_id: int,
) -> UserAccount | None:
    return database_session.get(UserAccount, user_account_id)

def get_user_account_by_email(
    database_session: Session,
    email: str,
) -> UserAccount | None:
    return database_session.scalar(select(UserAccount).where(UserAccount.email == email))

def get_user_account_by_agent_number(
    database_session: Session,
    agent_number: int,
) -> UserAccount | None:
    return database_session.scalar(
        select(UserAccount).where(UserAccount.agent_number == agent_number)
    )

def get_agent_by_id(
    database_session: Session,
    user_account_id: int,
) -> UserAccount | None:
    agent = database_session.get(UserAccount, user_account_id)
    if agent is None or agent.role != UserRole.AGENT:
        return None
    return agent

def list_agents(
    database_session: Session,
    *,
    include_inactive: bool = False,
) -> list[UserAccount]:
    query = select(UserAccount).where(UserAccount.role == UserRole.AGENT)
    if not include_inactive:
        query = query.where(UserAccount.is_active.is_(True))
    query = query.order_by(
        UserAccount.agent_number.is_(None).asc(),
        UserAccount.agent_number.asc(),
        UserAccount.user_account_id.asc(),
    )
    return list(database_session.scalars(query).all())

def add_user_account(
    database_session: Session,
    user_account: UserAccount,
) -> UserAccount:
    """Кладёт новый аккаунт в сессию (commit делает вызывающий)."""
    database_session.add(user_account)
    return user_account
