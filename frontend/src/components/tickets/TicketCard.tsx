import type { SupportTicket } from "@/types/api";
import { getCategoryLabel, getStatusLabel } from "@/lib/labels";

interface TicketCardProps {
  ticket: SupportTicket;
  onOpen: (ticket: SupportTicket) => void;
}

export function TicketCard({ ticket, onOpen }: TicketCardProps) {
  return (
    <button type="button" className="ticket-card" onClick={() => onOpen(ticket)}>
      <div className="ticket-card-top">
        <div className="ticket-card-content">
          <div className="ticket-card-number">Тикет №{ticket.support_ticket_id}</div>
          <div className="ticket-card-category">{getCategoryLabel(ticket.problem_reason)}</div>
        </div>
        <span className={`status-tag status-tag--${ticket.status}`}>
          {getStatusLabel(ticket.status)}
        </span>
      </div>
      <p className="ticket-card-description">{ticket.description}</p>
    </button>
  );
}
