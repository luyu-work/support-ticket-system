"use client";

import {
  FormEvent,
  PointerEvent as ReactPointerEvent,
  useEffect,
  useRef,
  useState,
} from "react";
import { ApiError, createTicket, fetchProblemReasons } from "@/lib/api";
import { MAX_TICKET_PHOTOS } from "@/lib/labels";
import type { ProblemReasonOption } from "@/types/api";

interface CreateTicketModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateTicketModal({ open, onClose, onCreated }: CreateTicketModalProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [reasons, setReasons] = useState<ProblemReasonOption[]>([]);
  const [reasonOpen, setReasonOpen] = useState(false);
  const [problemReason, setProblemReason] = useState("");
  const [description, setDescription] = useState("");
  const [photos, setPhotos] = useState<File[]>([]);
  const [photoPreviews, setPhotoPreviews] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"error" | "success" | "">("");
  const [loading, setLoading] = useState(false);
  const [formScrollable, setFormScrollable] = useState(false);

  useEffect(() => {
    if (!open) return;
    fetchProblemReasons()
      .then(setReasons)
      .catch(() => setMessage("Не удалось загрузить причины"));
  }, [open]);

  useEffect(() => {
    const urls = photos.map((file) => URL.createObjectURL(file));
    setPhotoPreviews(urls);
    return () => urls.forEach((url) => URL.revokeObjectURL(url));
  }, [photos]);

  useEffect(() => {
    if (!open) return;
    document.body.classList.add("modal-open");
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (reasonOpen) {
        setReasonOpen(false);
        return;
      }
      onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.classList.remove("modal-open");
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onClose, reasonOpen]);

  useEffect(() => {
    if (!open || !formRef.current || !dialogRef.current) return;
    const form = formRef.current;
    const dialog = dialogRef.current;
    const dialogMaxPx = parseFloat(getComputedStyle(dialog).maxHeight);
    const header = dialog.querySelector(".ticket-modal-header") as HTMLElement | null;
    const headerHeight = header?.getBoundingClientRect().height || 0;
    const available = dialogMaxPx - headerHeight;
    if (!Number.isFinite(available) || available <= 0) return;
    form.style.maxHeight = `${available}px`;
    setFormScrollable(form.scrollHeight > available + 2);
  }, [open, photos, description, problemReason, message]);

  function resetForm() {
    setProblemReason("");
    setDescription("");
    setPhotos([]);
    setMessage("");
    setMessageType("");
    setReasonOpen(false);
    if (textareaRef.current) textareaRef.current.style.height = "120px";
  }

  function handleClose() {
    resetForm();
    onClose();
  }

  function onPickPhotos(fileList: FileList | null) {
    if (!fileList) return;
    const incoming = Array.from(fileList);
    setPhotos((prev) => {
      const free = MAX_TICKET_PHOTOS - prev.length;
      return prev.concat(incoming.slice(0, free));
    });
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function startResize(event: ReactPointerEvent<HTMLButtonElement>) {
    const textarea = textareaRef.current;
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

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!problemReason) {
      setMessage("Выберите причину");
      setMessageType("error");
      return;
    }
    if (!description.trim()) {
      setMessage("Заполните описание");
      setMessageType("error");
      return;
    }

    setLoading(true);
    setMessage("Отправляем…");
    setMessageType("");
    try {
      await createTicket(problemReason, description.trim(), photos);
      resetForm();
      onCreated();
      onClose();
    } catch (error) {
      setMessageType("error");
      setMessage(error instanceof ApiError ? error.detail : "Сервер недоступен");
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  const selectedReasonLabel =
    reasons.find((item) => item.value === problemReason)?.label_ru || "Выберите причину";

  return (
    <div className="ticket-modal">
      <div className="ticket-modal-backdrop" onClick={handleClose} />
      <div
        ref={dialogRef}
        className="ticket-modal-dialog ticket-modal-dialog--wide"
        role="dialog"
        aria-modal
      >
        <div className="ticket-modal-header">
          <h2>Новый тикет</h2>
          <button type="button" className="icon-button" aria-label="Закрыть" onClick={handleClose}>
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

        <form
          ref={formRef}
          className={`create-ticket-form${formScrollable ? " is-scrollable" : ""}`}
          onSubmit={onSubmit}
          noValidate
        >
          <div className="field">
            <span className="field-label">
              Причина<span className="required-mark">*</span>
            </span>
            <div className="custom-select" data-open={reasonOpen ? "true" : "false"}>
              <button
                type="button"
                className="input-shell custom-select-trigger"
                aria-expanded={reasonOpen}
                onClick={() => setReasonOpen((v) => !v)}
              >
                <span
                  className={`custom-select-value${problemReason ? "" : " is-placeholder"}`}
                >
                  {selectedReasonLabel}
                </span>
                <svg className="select-chevron" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
                  <path
                    d="M15.8333 7.5L10 13.3333L4.16666 7.5"
                    stroke="#151515"
                    strokeOpacity="0.6"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
              {reasonOpen && (
                <div className="custom-select-dropdown" role="listbox">
                  {reasons.map((reason) => (
                    <button
                      key={reason.value}
                      type="button"
                      className={`custom-select-option${
                        problemReason === reason.value ? " is-selected" : ""
                      }`}
                      onClick={() => {
                        setProblemReason(reason.value);
                        setReasonOpen(false);
                      }}
                    >
                      {reason.label_ru}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="field field--description">
            <label className="field-label" htmlFor="description">
              Описание<span className="required-mark">*</span>
            </label>
            <div className="textarea-shell description-field">
              <textarea
                ref={textareaRef}
                id="description"
                name="description"
                rows={4}
                placeholder="Опишите, что произошло..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />
              <button
                type="button"
                className="textarea-resize-handle"
                aria-label="Изменить высоту поля описания"
                onPointerDown={startResize}
              >
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden>
                  <path d="M0.5 8.5L8.5 0.5M4.5 9.5L9.5 4.5" stroke="#151515" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          </div>

          <div className="field">
            <div className="field-label">Фотографии (необязательно, до {MAX_TICKET_PHOTOS} шт.)</div>
            <div className="photo-preview-list">
              {photoPreviews.map((url, index) => (
                <div key={url} className="photo-preview-tile">
                  <img src={url} alt="" />
                  <button
                    type="button"
                    className="photo-remove-button"
                    aria-label="Удалить фото"
                    onClick={() => setPhotos((prev) => prev.filter((_, i) => i !== index))}
                  >
                    ×
                  </button>
                </div>
              ))}
              {photos.length < MAX_TICKET_PHOTOS && (
                <button
                  type="button"
                  className="photo-add-tile"
                  aria-label="Добавить фото"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden>
                    <path
                      d="M8 16H16M16 16H24M16 16V24M16 16V8"
                      stroke="#151515"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              multiple
              hidden
              onChange={(e) => onPickPhotos(e.target.files)}
            />
          </div>

          <p className={`auth-message ${messageType}`} aria-live="polite">
            {message}
          </p>

          <button className="btn-submit-ticket" type="submit" disabled={loading}>
            Отправить тикет
          </button>
        </form>
      </div>
    </div>
  );
}
