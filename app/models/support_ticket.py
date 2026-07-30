from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import DatabaseModelBase
from app.models.enums import TicketStatus

if TYPE_CHECKING:
    from app.models.ticket_activity import TicketActivity
    from app.models.ticket_attachment import TicketAttachment
    from app.models.ticket_comment import TicketComment
    from app.models.user_account import UserAccount


class SupportTicket(DatabaseModelBase):
    """
    One support request from a client.
    Table name: support_tickets
    """

    __tablename__ = "support_tickets"

    support_ticket_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Short label in lists; problem_reason is the select value from the form
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_reason: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", native_enum=False, length=32),
        nullable=False,
        default=TicketStatus.IN_QUEUE,
        index=True,
    )

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    client_author_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.user_account_id"),
        nullable=False,
        index=True,
    )
    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_accounts.user_account_id"),
        nullable=True,
        index=True,
    )

    client_author: Mapped["UserAccount"] = relationship(
        back_populates="tickets_created",
        foreign_keys=[client_author_id],
    )
    assigned_agent: Mapped["UserAccount | None"] = relationship(
        back_populates="tickets_assigned",
        foreign_keys=[assigned_agent_id],
    )
    comments: Mapped[list["TicketComment"]] = relationship(
        back_populates="support_ticket",
        cascade="all, delete-orphan",
    )
    activity_events: Mapped[list["TicketActivity"]] = relationship(
        back_populates="support_ticket",
        cascade="all, delete-orphan",
        order_by="TicketActivity.created_at",
    )
    attachments: Mapped[list["TicketAttachment"]] = relationship(
        back_populates="support_ticket",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<SupportTicket id={self.support_ticket_id} "
            f"status={self.status} reason={self.problem_reason!r}>"
        )
