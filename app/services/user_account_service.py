"""Create and authenticate user accounts."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_plain_password, verify_plain_password
from app.models import UserAccount, UserRole


class EmailAlreadyRegisteredError(Exception):
    """Raised when registration email is already in the database."""


class InvalidCredentialsError(Exception):
    """Raised when email/password do not match an active account."""


class InactiveUserAccountError(Exception):
    """Raised when the account exists but is disabled."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_account_by_email(database_session: Session, email: str) -> UserAccount | None:
    normalized_email = normalize_email(email)
    return database_session.scalar(
        select(UserAccount).where(UserAccount.email == normalized_email)
    )


def get_user_account_by_id(
    database_session: Session,
    user_account_id: int,
) -> UserAccount | None:
    return database_session.get(UserAccount, user_account_id)


def register_client_account(
    database_session: Session,
    *,
    email: str,
    full_name: str,
    plain_password: str,
) -> UserAccount:
    """
    Register a new client (обычный пользователь).
    Admin/agent cannot be created through public registration.
    """
    normalized_email = normalize_email(email)
    existing_account = get_user_account_by_email(database_session, normalized_email)
    if existing_account is not None:
        raise EmailAlreadyRegisteredError(normalized_email)

    new_client = UserAccount(
        email=normalized_email,
        full_name=full_name.strip(),
        hashed_password=hash_plain_password(plain_password),
        role=UserRole.CLIENT,
        is_active=True,
        is_online=False,
    )
    database_session.add(new_client)
    database_session.commit()
    database_session.refresh(new_client)
    return new_client


def authenticate_user_account(
    database_session: Session,
    *,
    email: str,
    plain_password: str,
) -> UserAccount:
    """Check email + password. Works for client, agent, and admin."""
    user_account = get_user_account_by_email(database_session, email)
    if user_account is None:
        raise InvalidCredentialsError

    if not verify_plain_password(plain_password, user_account.hashed_password):
        raise InvalidCredentialsError

    if not user_account.is_active:
        raise InactiveUserAccountError

    return user_account


def ensure_staff_user_account(
    database_session: Session,
    *,
    email: str,
    full_name: str,
    plain_password: str,
    role: UserRole,
) -> UserAccount:
    """
    Create staff account if missing.
    If the email already exists, refresh name/password/role from seed settings.
    """
    if role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise ValueError("ensure_staff_user_account is only for admin or agent")

    existing_account = get_user_account_by_email(database_session, email)
    if existing_account is not None:
        existing_account.full_name = full_name.strip()
        existing_account.hashed_password = hash_plain_password(plain_password)
        existing_account.role = role
        existing_account.is_active = True
        database_session.commit()
        database_session.refresh(existing_account)
        return existing_account

    staff_account = UserAccount(
        email=normalize_email(email),
        full_name=full_name.strip(),
        hashed_password=hash_plain_password(plain_password),
        role=role,
        is_active=True,
        is_online=False,
    )
    database_session.add(staff_account)
    database_session.commit()
    database_session.refresh(staff_account)
    return staff_account
