"""Tests for DB models: create rows, links, defaults, business enums."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    MAX_ATTACHMENTS_PER_TICKET,
    SupportTicket,
    TicketAttachment,
    TicketComment,
    TicketProblemReason,
    TicketStatus,
    UserAccount,
    UserRole,
)


def _create_client(database_session: Session, email: str = "client@example.com") -> UserAccount:
    client = UserAccount(
        email=email,
        full_name="Иван Клиентов",
        hashed_password="hashed-demo-password",
        role=UserRole.CLIENT,
    )
    database_session.add(client)
    database_session.commit()
    database_session.refresh(client)
    return client


def _create_agent(database_session: Session, email: str = "agent@example.com") -> UserAccount:
    agent = UserAccount(
        email=email,
        full_name="Анна Агентова",
        hashed_password="hashed-demo-password",
        role=UserRole.AGENT,
        is_online=True,
    )
    database_session.add(agent)
    database_session.commit()
    database_session.refresh(agent)
    return agent


def test_create_user_account_with_client_role(database_session: Session) -> None:
    client = _create_client(database_session)

    assert client.user_account_id is not None
    assert client.email == "client@example.com"
    assert client.role == UserRole.CLIENT
    assert client.is_active is True
    assert client.is_online is False


def test_user_email_must_be_unique(database_session: Session) -> None:
    _create_client(database_session, email="same@example.com")

    duplicate = UserAccount(
        email="same@example.com",
        full_name="Другой Человек",
        hashed_password="hashed-demo-password",
        role=UserRole.CLIENT,
    )
    database_session.add(duplicate)

    with pytest.raises(IntegrityError):
        database_session.commit()


def test_support_ticket_defaults_to_in_queue(database_session: Session) -> None:
    client = _create_client(database_session)

    ticket = SupportTicket(
        title="Не могу войти",
        problem_reason=TicketProblemReason.LOGIN_ISSUE.value,
        description="После смены пароля вход не работает",
        client_author_id=client.user_account_id,
    )
    database_session.add(ticket)
    database_session.commit()
    database_session.refresh(ticket)

    assert ticket.support_ticket_id is not None
    assert ticket.status == TicketStatus.IN_QUEUE
    assert ticket.assigned_agent_id is None
    assert ticket.client_author.email == "client@example.com"


def test_assign_agent_and_move_ticket_to_in_progress(database_session: Session) -> None:
    client = _create_client(database_session)
    agent = _create_agent(database_session)

    ticket = SupportTicket(
        title="Ошибка оплаты",
        problem_reason=TicketProblemReason.PAYMENT_ISSUE.value,
        description="Списались деньги дважды",
        client_author_id=client.user_account_id,
    )
    database_session.add(ticket)
    database_session.commit()

    ticket.assigned_agent_id = agent.user_account_id
    ticket.status = TicketStatus.IN_PROGRESS
    database_session.commit()
    database_session.refresh(ticket)

    assert ticket.status == TicketStatus.IN_PROGRESS
    assert ticket.assigned_agent.email == "agent@example.com"
    assert agent.tickets_assigned[0].support_ticket_id == ticket.support_ticket_id


def test_ticket_comment_links_author_and_ticket(database_session: Session) -> None:
    client = _create_client(database_session)
    agent = _create_agent(database_session)

    ticket = SupportTicket(
        title="Баг в интерфейсе",
        problem_reason=TicketProblemReason.BUG_REPORT.value,
        description="Кнопка не нажимается",
        client_author_id=client.user_account_id,
        assigned_agent_id=agent.user_account_id,
        status=TicketStatus.IN_PROGRESS,
    )
    database_session.add(ticket)
    database_session.commit()

    comment = TicketComment(
        comment_text="Проверили, передаём в фикс",
        support_ticket_id=ticket.support_ticket_id,
        author_user_id=agent.user_account_id,
    )
    database_session.add(comment)
    database_session.commit()
    database_session.refresh(ticket)

    assert len(ticket.comments) == 1
    assert ticket.comments[0].comment_text == "Проверили, передаём в фикс"
    assert ticket.comments[0].comment_author.role == UserRole.AGENT


def test_ticket_attachments_belong_to_ticket(database_session: Session) -> None:
    client = _create_client(database_session)
    ticket = SupportTicket(
        title="Скриншот ошибки",
        problem_reason=TicketProblemReason.OTHER.value,
        description="Во вложении фото",
        client_author_id=client.user_account_id,
    )
    database_session.add(ticket)
    database_session.commit()

    first_photo = TicketAttachment(
        support_ticket_id=ticket.support_ticket_id,
        storage_path="uploads/tickets/1/photo_1.jpg",
        original_file_name="photo_1.jpg",
    )
    second_photo = TicketAttachment(
        support_ticket_id=ticket.support_ticket_id,
        storage_path="uploads/tickets/1/photo_2.jpg",
        original_file_name="photo_2.jpg",
    )
    database_session.add_all([first_photo, second_photo])
    database_session.commit()
    database_session.refresh(ticket)

    assert len(ticket.attachments) == 2
    file_names = {item.original_file_name for item in ticket.attachments}
    assert file_names == {"photo_1.jpg", "photo_2.jpg"}
    assert MAX_ATTACHMENTS_PER_TICKET == 10


def test_filter_tickets_by_status_and_problem_reason(database_session: Session) -> None:
    client = _create_client(database_session)

    database_session.add_all(
        [
            SupportTicket(
                title="A",
                problem_reason=TicketProblemReason.LOGIN_ISSUE.value,
                description="d1",
                client_author_id=client.user_account_id,
                status=TicketStatus.IN_QUEUE,
            ),
            SupportTicket(
                title="B",
                problem_reason=TicketProblemReason.PAYMENT_ISSUE.value,
                description="d2",
                client_author_id=client.user_account_id,
                status=TicketStatus.IN_QUEUE,
            ),
            SupportTicket(
                title="C",
                problem_reason=TicketProblemReason.LOGIN_ISSUE.value,
                description="d3",
                client_author_id=client.user_account_id,
                status=TicketStatus.CLOSED,
            ),
        ]
    )
    database_session.commit()

    open_login_tickets = database_session.scalars(
        select(SupportTicket).where(
            SupportTicket.status == TicketStatus.IN_QUEUE,
            SupportTicket.problem_reason == TicketProblemReason.LOGIN_ISSUE.value,
        )
    ).all()

    assert len(open_login_tickets) == 1
    assert open_login_tickets[0].title == "A"


def test_ticket_status_values_match_business_rules() -> None:
    assert TicketStatus.IN_QUEUE.value == "in_queue"
    assert TicketStatus.IMPORTANT.value == "important"
    assert TicketStatus.IN_PROGRESS.value == "in_progress"
    assert TicketStatus.CLOSED.value == "closed"
    assert TicketStatus.TRANSFERRED_TO_ENGINEERS.value == "transferred_to_engineers"


def test_user_role_values_match_business_rules() -> None:
    assert {role.value for role in UserRole} == {"client", "agent", "admin"}
