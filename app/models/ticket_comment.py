from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import DatabaseModelBase

if TYPE_CHECKING:
    from app.models.support_ticket import SupportTicket
    from app.models.user_account import UserAccount


class TicketComment(DatabaseModelBase):
    """
    Comment on a ticket (usually from an agent).
    Table name: ticket_comments
    """

    __tablename__ = "ticket_comments"

    ticket_comment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)

    support_ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.support_ticket_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_user_id: Mapped[int] = mapped_column(
        ForeignKey("user_accounts.user_account_id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    support_ticket: Mapped["SupportTicket"] = relationship(back_populates="comments")
    comment_author: Mapped["UserAccount"] = relationship(back_populates="ticket_comments")

    def __repr__(self) -> str:
        return (
            f"<TicketComment id={self.ticket_comment_id} "
            f"ticket={self.support_ticket_id}>"
        )
