from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import DatabaseModelBase
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.support_ticket import SupportTicket
    from app.models.ticket_comment import TicketComment


class UserAccount(DatabaseModelBase):
    """
    Account in the ticket system: client, agent, or admin.
    Table name: user_accounts
    """

    __tablename__ = "user_accounts"

    user_account_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, length=32),
        nullable=False,
        default=UserRole.CLIENT,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # For admin MVP later: how many agents look "online"
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tickets_created: Mapped[list["SupportTicket"]] = relationship(
        back_populates="client_author",
        foreign_keys="SupportTicket.client_author_id",
    )
    tickets_assigned: Mapped[list["SupportTicket"]] = relationship(
        back_populates="assigned_agent",
        foreign_keys="SupportTicket.assigned_agent_id",
    )
    ticket_comments: Mapped[list["TicketComment"]] = relationship(
        back_populates="comment_author",
    )

    def __repr__(self) -> str:
        return (
            f"<UserAccount id={self.user_account_id} "
            f"email={self.email!r} role={self.role}>"
        )
