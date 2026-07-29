"""Role helpers shared by deps and API layers."""

from app.models import UserAccount, UserRole


def role_value(user_account: UserAccount) -> str:
    role = user_account.role
    return role.value if hasattr(role, "value") else str(role)


def is_staff(user_account: UserAccount) -> bool:
    return role_value(user_account) in {UserRole.AGENT.value, UserRole.ADMIN.value}


def is_agent(user_account: UserAccount) -> bool:
    return role_value(user_account) == UserRole.AGENT.value


def is_admin(user_account: UserAccount) -> bool:
    return role_value(user_account) == UserRole.ADMIN.value


def is_client(user_account: UserAccount) -> bool:
    return role_value(user_account) == UserRole.CLIENT.value
