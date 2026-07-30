"""История событий по тикетам."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import DatabaseModelBase
from app.models.enums import TicketActivityEventType

if TYPE_CHECKING:
    from app.models.support_ticket import SupportTicket
    from app.models.user_account import UserAccount

class TicketActivity(DatabaseModelBase):
    """
    Одно событие в истории тикета (создан, взят, закрыт…).
    Таблица: ticket_activities
    """

    __tablename__ = "ticket_activities"

    ticket_activity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    event_type: Mapped[TicketActivityEventType] = mapped_column(
        Enum(
            TicketActivityEventType,
            name="ticket_activity_event_type",
            native_enum=False,
            length=40,
        ),
        nullable=False,
        index=True,
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    support_ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.support_ticket_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_accounts.user_account_id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    support_ticket: Mapped["SupportTicket"] = relationship(back_populates="activity_events")
    actor: Mapped["UserAccount | None"] = relationship()

    def __repr__(self) -> str:
        return (
            f"<TicketActivity id={self.ticket_activity_id} "
            f"type={self.event_type} ticket={self.support_ticket_id}>"
        )
