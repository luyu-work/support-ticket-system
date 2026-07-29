from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import DatabaseModelBase

if TYPE_CHECKING:
    from app.models.support_ticket import SupportTicket

# Business rule (enforced in services later, not only in DB): max 10 photos per ticket
MAX_ATTACHMENTS_PER_TICKET = 10


class TicketAttachment(DatabaseModelBase):
    """
    One photo/file attached to a ticket (optional, up to 10 per ticket).
    Table name: ticket_attachments
    """

    __tablename__ = "ticket_attachments"

    ticket_attachment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    support_ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.support_ticket_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Where the file is stored on disk / object storage (path or key)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    support_ticket: Mapped["SupportTicket"] = relationship(back_populates="attachments")

    def __repr__(self) -> str:
        return (
            f"<TicketAttachment id={self.ticket_attachment_id} "
            f"ticket={self.support_ticket_id} file={self.original_file_name!r}>"
        )
