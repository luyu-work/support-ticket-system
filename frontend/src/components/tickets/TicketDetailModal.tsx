"use client";

import {
  PointerEvent as ReactPointerEvent,
  useEffect,
  useRef,
  useState,
} from "react";
import type { SupportTicket } from "@/types/api";
import {
  ApiError,
  closeTicket,
  fetchTicketAttachmentBlob,
  fetchTicketDetail,
  transferTicketToEngineers,
} from "@/lib/api";
import { formatTicketCreatedAt } from "@/lib/auth-storage";
import { getCategoryLabel, getStatusLabel } from "@/lib/labels";
import { PhotoLightbox } from "@/components/tickets/PhotoLightbox";

type AgentStep = "view" | "closeConfirm";
type ModalPanel = "details" | "logs";

interface TicketDetailModalProps {
  ticket: SupportTicket | null;
  open: boolean;
  onClose: () => void;

  lockUntilResolved?: boolean;

  agentActions?: boolean;

  showTicketLogs?: boolean;
  onResolved?: (ticket: SupportTicket) => void;
}

export function TicketDetailModal({
  ticket,
  open,
  onClose,
  lockUntilResolved = false,
  agentActions = false,
  showTicketLogs = false,
  onResolved,
}: TicketDetailModalProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const commentRef = useRef<HTMLTextAreaElement>(null);
  const [detail, setDetail] = useState<SupportTicket | null>(null);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const [agentStep, setAgentStep] = useState<AgentStep>("view");
  const [closeComment, setCloseComment] = useState("");
  const [panel, setPanel] = useState<ModalPanel>("details");

  useEffect(() => {
    if (!open || !ticket) {
      setDetail(null);
      setIsLocked(false);
      setActionError("");
      setAgentStep("view");
      setCloseComment("");
      setPanel("details");
      setPhotoUrls((prev) => {
        prev.forEach((url) => URL.revokeObjectURL(url));
        return [];
      });
      return;
    }

    setIsLocked(lockUntilResolved);
    setActionError("");
    setAgentStep("view");
    setCloseComment("");
    setPanel("details");

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
  }, [open, ticket, lockUntilResolved]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (lightboxSrc) {
        setLightboxSrc(null);
        return;
      }
      if (panel === "logs") {
        setPanel("details");
        return;
      }
      if (isLocked) {
        if (agentStep === "closeConfirm") {
          setAgentStep("view");
          setActionError("");
        }
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
  }, [open, onClose, lightboxSrc, isLocked, agentStep, panel]);

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
  }, [open, detail, photoUrls, isLocked, actionError, agentStep, closeComment, panel]);

  function startCommentResize(event: ReactPointerEvent<HTMLButtonElement>) {
    const textarea = commentRef.current;
    if (!textarea) return;
    event.preventDefault();
    const startY = event.clientY;
    const startHeight = textarea.getBoundingClientRect().height;
    const minHeight = 120;
    const maxHeight = 193;

    const onMove = (moveEvent: PointerEvent) => {
      const next = Math.max(
        minHeight,
        Math.min(maxHeight, startHeight + (moveEvent.clientY - startY)),
      );
      textarea.style.height = `${next}px`;
    };
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  async function handleConfirmCloseTicket() {
    if (!detail && !ticket) return;
    const comment = closeComment.trim();
    if (!comment) {
      setActionError("Заполните комментарий");
      return;
    }
    const id = (detail || ticket)!.support_ticket_id;
    setActionLoading(true);
    setActionError("");
    try {
      const updated = await closeTicket(id, comment);
      setDetail(updated);
      setIsLocked(false);
      setAgentStep("view");
      setCloseComment("");
      onResolved?.(updated);
      onClose();
    } catch (error) {
      setActionError(error instanceof ApiError ? error.detail : "Не удалось закрыть тикет");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleTransferToEngineers() {
    if (!detail && !ticket) return;
    const id = (detail || ticket)!.support_ticket_id;
    setActionLoading(true);
    setActionError("");
    try {
      const updated = await transferTicketToEngineers(id);
      setDetail(updated);
      setIsLocked(false);
      onResolved?.(updated);
      onClose();
    } catch (error) {
      setActionError(
        error instanceof ApiError ? error.detail : "Не удалось передать инженерам",
      );
    } finally {
      setActionLoading(false);
    }
  }

  function requestClose() {
    if (isLocked) return;
    onClose();
  }

  function cancelCloseConfirm() {
    setAgentStep("view");
    setCloseComment("");
    setActionError("");
    if (commentRef.current) commentRef.current.style.height = "120px";
  }

  function toggleLogsPanel() {
    setPanel((prev) => (prev === "logs" ? "details" : "logs"));
    setActionError("");
  }

  if (!open || !ticket) return null;
  const view = detail || ticket;
  const canActOnTicket =
    agentActions &&
    view.status !== "closed" &&
    view.status !== "transferred_to_engineers";
  const isCloseConfirm = agentActions && agentStep === "closeConfirm";
  const isLogsPanel = showTicketLogs && panel === "logs" && !isCloseConfirm;
  const comments = view.comments || [];
  const activityLog = view.activity_log || [];

  const showCreatedAt = showTicketLogs && !isCloseConfirm && !isLogsPanel;

  return (
    <>
      <div className="ticket-modal">
        <div
          className="ticket-modal-backdrop"
          onClick={requestClose}
          style={isLocked ? { cursor: "default" } : undefined}
        />
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
            <div className="ticket-detail-header-actions">
              {showTicketLogs && !isCloseConfirm && (
                <button
                  type="button"
                  className={`ticket-logs-button${isLogsPanel ? " is-active" : ""}`}
                  onClick={toggleLogsPanel}
                  aria-pressed={isLogsPanel}
                >
                  {isLogsPanel ? "Назад" : "Логи"}
                </button>
              )}
              {!isLocked && (
                <button
                  type="button"
                  className="icon-button"
                  aria-label="Закрыть"
                  onClick={requestClose}
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                    <path
                      d="M12 12L8.00001 8.00001M8.00001 8.00001L4 4M8.00001 8.00001L12 4M8.00001 8.00001L4 12"
                      stroke="#333333"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
              )}
            </div>
          </div>

          <div ref={bodyRef} className="ticket-detail-body">
            {isLogsPanel ? (
              <div className="ticket-logs-panel">
                <div className="ticket-logs-panel-title">История тикета</div>
                {activityLog.length === 0 ? (
                  <p className="ticket-logs-empty">Пока нет записей в логе</p>
                ) : (
                  <ul className="ticket-activity-log">
                    {activityLog.map((event) => {

                      const details =
                        event.details &&
                        event.event_type !== "closed" &&
                        event.details.trim() !== (event.actor_full_name || "").trim()
                          ? event.details
                          : null;

                      return (
                        <li key={event.ticket_activity_id} className="ticket-activity-item">
                          <div className="ticket-activity-marker" aria-hidden>
                            <svg
                              className="ticket-activity-dot"
                              width="8"
                              height="8"
                              viewBox="0 0 8 8"
                              fill="none"
                            >
                              <circle cx="4" cy="4" r="4" fill="#3761F3" />
                            </svg>
                          </div>
                          <div className="ticket-activity-time">
                            {formatTicketCreatedAt(event.created_at)}
                          </div>
                          <div className="ticket-activity-body">
                            <div className="ticket-activity-label">{event.event_label_ru}</div>
                            {event.actor_full_name && (
                              <div className="ticket-activity-actor">{event.actor_full_name}</div>
                            )}
                            {details && (
                              <div className="ticket-activity-details">{details}</div>
                            )}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            ) : (
              <>
                {showCreatedAt && (
                  <div className="ticket-detail-field">
                    <div className="ticket-detail-label">Время создания</div>
                    <div className="ticket-detail-value">
                      {formatTicketCreatedAt(view.created_at)}
                    </div>
                  </div>
                )}

                {!isCloseConfirm && (
                  <div className="ticket-detail-field">
                    <div className="ticket-detail-label">Категория</div>
                    <div className="ticket-detail-value">
                      {getCategoryLabel(view.problem_reason)}
                    </div>
                  </div>
                )}

                <div className="ticket-detail-field">
                  <div className="ticket-detail-label">Описание</div>
                  <div className="ticket-detail-value">{view.description}</div>
                </div>

                {photoUrls.length > 0 && (
                  <div className="ticket-detail-field ticket-detail-field--photos">
                    <div className="ticket-detail-label">Фотографии</div>
                    <div className="ticket-detail-photos">
                      {photoUrls.map((url) => (

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

                {!isCloseConfirm &&
                  comments.map((comment) => (
                    <div key={comment.ticket_comment_id} className="ticket-support-comment">
                      <div className="ticket-support-comment-label">
                        {showTicketLogs
                          ? "Комментарий агента"
                          : "Комментарий от тех. поддержки"}
                      </div>
                      <div className="ticket-support-comment-text">{comment.comment_text}</div>
                      <div className="ticket-support-comment-meta">
                        {comment.author_full_name || "Агент"},{" "}
                        {formatTicketCreatedAt(comment.created_at)}
                      </div>
                    </div>
                  ))}

                {isCloseConfirm && (
                  <div className="field field--description ticket-close-comment-field">
                    <label className="field-label" htmlFor="close-comment">
                      Комментарий<span className="required-mark">*</span>
                    </label>
                    <div className="textarea-shell description-field">
                      <textarea
                        ref={commentRef}
                        id="close-comment"
                        name="close-comment"
                        rows={4}
                        placeholder="Опишите, итог работы..."
                        value={closeComment}
                        onChange={(e) => setCloseComment(e.target.value)}
                        required
                        disabled={actionLoading}
                      />
                      <button
                        type="button"
                        className="textarea-resize-handle"
                        aria-label="Изменить высоту поля комментария"
                        onPointerDown={startCommentResize}
                      >
                        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden>
                          <path
                            d="M0.5 8.5L8.5 0.5M4.5 9.5L9.5 4.5"
                            stroke="#151515"
                            strokeLinecap="round"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                )}

                {canActOnTicket && !isCloseConfirm && (
                  <div className="ticket-agent-actions">
                    {actionError && <p className="auth-message error">{actionError}</p>}
                    <div className="ticket-agent-actions-row">
                      <button
                        type="button"
                        className="btn-secondary-ticket"
                        disabled={actionLoading}
                        onClick={() => void handleTransferToEngineers()}
                      >
                        Передать инженерам
                      </button>
                      <button
                        type="button"
                        className="btn-submit-ticket"
                        disabled={actionLoading}
                        onClick={() => {
                          setActionError("");
                          setPanel("details");
                          setAgentStep("closeConfirm");
                        }}
                      >
                        Закрыть тикет
                      </button>
                    </div>
                  </div>
                )}

                {canActOnTicket && isCloseConfirm && (
                  <div className="ticket-agent-actions">
                    {actionError && <p className="auth-message error">{actionError}</p>}
                    <div className="ticket-agent-actions-row">
                      <button
                        type="button"
                        className="btn-secondary-ticket"
                        disabled={actionLoading}
                        onClick={cancelCloseConfirm}
                      >
                        Отменить
                      </button>
                      <button
                        type="button"
                        className="btn-submit-ticket"
                        disabled={actionLoading}
                        onClick={() => void handleConfirmCloseTicket()}
                      >
                        Подтвердить
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      <PhotoLightbox src={lightboxSrc} onClose={() => setLightboxSrc(null)} />
    </>
  );
}
