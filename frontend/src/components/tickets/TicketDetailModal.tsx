"use client";

import { useEffect, useRef, useState } from "react";
import type { SupportTicket } from "@/types/api";
import { fetchTicketAttachmentBlob, fetchTicketDetail } from "@/lib/api";
import { getCategoryLabel, getStatusLabel } from "@/lib/labels";
import { PhotoLightbox } from "@/components/tickets/PhotoLightbox";

interface TicketDetailModalProps {
  ticket: SupportTicket | null;
  open: boolean;
  onClose: () => void;
}

export function TicketDetailModal({ ticket, open, onClose }: TicketDetailModalProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const [detail, setDetail] = useState<SupportTicket | null>(null);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !ticket) {
      setDetail(null);
      setPhotoUrls((prev) => {
        prev.forEach((url) => URL.revokeObjectURL(url));
        return [];
      });
      return;
    }

    let cancelled = false;
    const objectUrls: string[] = [];

    (async () => {
      try {
        const fresh = await fetchTicketDetail(ticket.support_ticket_id);
        if (cancelled) return;
        setDetail(fresh);

        const urls: string[] = [];
        for (const attachment of fresh.attachments || []) {
          try {
            const blob = await fetchTicketAttachmentBlob(
              fresh.support_ticket_id,
              attachment.ticket_attachment_id,
            );
            const url = URL.createObjectURL(blob);
            objectUrls.push(url);
            urls.push(url);
          } catch {
            /* skip */
          }
        }
        if (!cancelled) setPhotoUrls(urls);
      } catch {
        if (!cancelled) setDetail(ticket);
      }
    })();

    return () => {
      cancelled = true;
      objectUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [open, ticket]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (lightboxSrc) {
        setLightboxSrc(null);
        return;
      }
      onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.classList.add("modal-open");
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.classList.remove("modal-open");
    };
  }, [open, onClose, lightboxSrc]);

  useEffect(() => {
    if (!open || !bodyRef.current || !dialogRef.current) return;
    const body = bodyRef.current;
    const dialog = dialogRef.current;
    const dialogMaxPx = parseFloat(getComputedStyle(dialog).maxHeight);
    const header = dialog.querySelector(".ticket-modal-header") as HTMLElement | null;
    const headerHeight = header?.getBoundingClientRect().height || 0;
    const available = dialogMaxPx - headerHeight;
    if (!Number.isFinite(available) || available <= 0) return;
    body.style.maxHeight = `${available}px`;
    body.classList.toggle("is-scrollable", body.scrollHeight > available + 2);
  }, [open, detail, photoUrls]);

  if (!open || !ticket) return null;
  const view = detail || ticket;

  return (
    <>
      <div className="ticket-modal">
        <div className="ticket-modal-backdrop" onClick={onClose} />
        <div
          ref={dialogRef}
          className="ticket-modal-dialog ticket-modal-dialog--wide"
          role="dialog"
          aria-modal
        >
          <div className="ticket-modal-header ticket-detail-header">
            <div className="ticket-detail-header-main">
              <h2>Тикет №{view.support_ticket_id}</h2>
              <span className={`status-tag status-tag--${view.status}`}>
                {getStatusLabel(view.status)}
              </span>
            </div>
            <button type="button" className="icon-button" aria-label="Закрыть" onClick={onClose}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                <path
                  d="M12 12L8.00001 8.00001M8.00001 8.00001L4 4M8.00001 8.00001L12 4M8.00001 8.00001L4 12"
                  stroke="#333333"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>

          <div ref={bodyRef} className="ticket-detail-body">
            <div className="ticket-detail-field">
              <div className="ticket-detail-label">Категория</div>
              <div className="ticket-detail-value">{getCategoryLabel(view.problem_reason)}</div>
            </div>
            <div className="ticket-detail-field">
              <div className="ticket-detail-label">Описание</div>
              <div className="ticket-detail-value">{view.description}</div>
            </div>
            {photoUrls.length > 0 && (
              <div className="ticket-detail-field">
                <div className="ticket-detail-label">Фотографии</div>
                <div className="ticket-detail-photos">
                  {photoUrls.map((url) => (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      key={url}
                      className="ticket-detail-photo"
                      src={url}
                      alt="Фото тикета"
                      onClick={() => setLightboxSrc(url)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <PhotoLightbox src={lightboxSrc} onClose={() => setLightboxSrc(null)} />
    </>
  );
}
