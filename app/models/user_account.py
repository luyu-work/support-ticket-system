from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
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
    # Agent presence for staff UIs
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Agent-only fields (null for client/admin)
    agent_number: Mapped[int | None] = mapped_column(
        Integer,
        unique=True,
        nullable=True,
        index=True,
    )
    # JSON list of weekday indices: 0=Mon … 6=Sun, e.g. "[0,1,2,3,4]"
    work_days: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "HH:MM" 24h local
    work_time_start: Mapped[str | None] = mapped_column(String(5), nullable=True)
    work_time_end: Mapped[str | None] = mapped_column(String(5), nullable=True)
    # Last password set by admin (for admin UI only; login still uses hashed_password)
    admin_visible_password: Mapped[str | None] = mapped_column(String(128), nullable=True)

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
        return f"<UserAccount id={self.user_account_id} email={self.email!r} role={self.role}>"
