"use client";

import {
  FormEvent,
  PointerEvent as ReactPointerEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { AgentAdmin } from "@/types/api";
import {
  ApiError,
  createAgent,
  deleteAgent,
  updateAgent,
} from "@/lib/api";

const WEEKDAYS = [
  { id: 0, short: "Пн", full: "Понедельник" },
  { id: 1, short: "Вт", full: "Вторник" },
  { id: 2, short: "Ср", full: "Среда" },
  { id: 3, short: "Чт", full: "Четверг" },
  { id: 4, short: "Пт", full: "Пятница" },
  { id: 5, short: "Сб", full: "Суббота" },
  { id: 6, short: "Вс", full: "Воскресенье" },
] as const;

const PRESETS = [
  { id: "weekdays", label: "Пн–Пт", days: [0, 1, 2, 3, 4] },
  { id: "all", label: "Все дни", days: [0, 1, 2, 3, 4, 5, 6] },
  { id: "weekend", label: "Сб–Вс", days: [5, 6] },
] as const;

function minutesToLabel(total: number): string {
  const clamped = Math.max(0, Math.min(24 * 60, total));
  const hours = Math.floor(clamped / 60) % 24;
  const minutes = clamped % 60;
  // allow 24:00 as end of day only when total === 24*60 — map to 23:59 for API
  if (total >= 24 * 60) return "23:59";
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function labelToMinutes(label: string): number {
  const [h, m] = label.split(":").map(Number);
  if (Number.isNaN(h) || Number.isNaN(m)) return 9 * 60;
  return Math.max(0, Math.min(23 * 60 + 59, h * 60 + m));
}

/** Accept "9:00", "09:00", "9.00", "900" → HH:MM or null if invalid. */
function parseTimeInput(raw: string): string | null {
  const text = raw.trim().replace(".", ":").replace(",", ":");
  if (!text) return null;
  let hour: number;
  let minute: number;
  if (/^\d{1,2}:\d{1,2}$/.test(text)) {
    const [h, m] = text.split(":").map(Number);
    hour = h;
    minute = m;
  } else if (/^\d{3,4}$/.test(text)) {
    const padded = text.padStart(4, "0");
    hour = Number(padded.slice(0, 2));
    minute = Number(padded.slice(2));
  } else if (/^\d{1,2}$/.test(text)) {
    hour = Number(text);
    minute = 0;
  } else {
    return null;
  }
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return null;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function daysLabel(days: number[]): string {
  const sorted = [...days].sort((a, b) => a - b);
  if (sorted.length === 0) return "не выбрано";
  if (sorted.join() === "0,1,2,3,4") return "Пн–Пт";
  if (sorted.join() === "0,1,2,3,4,5,6") return "ежедневно";
  if (sorted.join() === "5,6") return "Сб–Вс";
  return sorted.map((d) => WEEKDAYS[d]?.short || String(d)).join(", ");
}

interface AgentEditorModalProps {
  open: boolean;
  agent: AgentAdmin | null;
  mode: "create" | "edit";
  onClose: () => void;
  onSaved: () => void;
}

export function AgentEditorModal({
  open,
  agent,
  mode,
  onClose,
  onSaved,
}: AgentEditorModalProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const dragKind = useRef<"start" | "end" | null>(null);

  const [fullName, setFullName] = useState("");
  const [agentNumber, setAgentNumber] = useState("1");
  const [password, setPassword] = useState("");
  const [workDays, setWorkDays] = useState<number[]>([0, 1, 2, 3, 4]);
  const [startMin, setStartMin] = useState(9 * 60);
  const [endMin, setEndMin] = useState(18 * 60);
  const [startText, setStartText] = useState("09:00");
  const [endText, setEndText] = useState("18:00");
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"error" | "">("");
  const [loading, setLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const startMinRef = useRef(startMin);
  const endMinRef = useRef(endMin);
  startMinRef.current = startMin;
  endMinRef.current = endMin;

  function setStartMinutes(next: number) {
    const clamped = Math.min(next, endMinRef.current - 15);
    setStartMin(clamped);
    setStartText(minutesToLabel(clamped));
    startMinRef.current = clamped;
  }

  function setEndMinutes(next: number) {
    const clamped = Math.max(next, startMinRef.current + 15);
    setEndMin(clamped);
    setEndText(minutesToLabel(clamped));
    endMinRef.current = clamped;
  }

  useEffect(() => {
    if (!open) return;
    setMessage("");
    setMessageType("");
    setConfirmDelete(false);
    setPassword("");
    if (mode === "edit" && agent) {
      setFullName(agent.full_name);
      setAgentNumber(String(agent.agent_number ?? ""));
      setWorkDays(agent.work_days.length ? agent.work_days : [0, 1, 2, 3, 4]);
      const start = labelToMinutes(agent.work_time_start || "09:00");
      const end = labelToMinutes(agent.work_time_end || "18:00");
      setStartMin(start);
      setEndMin(end);
      setStartText(minutesToLabel(start));
      setEndText(minutesToLabel(end));
    } else {
      setFullName("");
      setAgentNumber("");
      setWorkDays([0, 1, 2, 3, 4]);
      setStartMin(9 * 60);
      setEndMin(18 * 60);
      setStartText("09:00");
      setEndText("18:00");
    }
  }, [open, mode, agent]);

  useEffect(() => {
    if (!open) return;
    document.body.classList.add("modal-open");
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.classList.remove("modal-open");
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  useEffect(() => {
    if (!open || !formRef.current || !dialogRef.current) return;
    const body = formRef.current;
    const dialog = dialogRef.current;
    const dialogMaxPx = parseFloat(getComputedStyle(dialog).maxHeight);
    const header = dialog.querySelector(".ticket-modal-header") as HTMLElement | null;
    const headerHeight = header?.getBoundingClientRect().height || 0;
    const available = dialogMaxPx - headerHeight;
    if (!Number.isFinite(available) || available <= 0) return;
    body.style.maxHeight = `${available}px`;
    body.classList.toggle("is-scrollable", body.scrollHeight > available + 2);
  }, [open, fullName, workDays, startMin, endMin, message, confirmDelete]);

  const startPct = (startMin / (24 * 60)) * 100;
  const endPct = (endMin / (24 * 60)) * 100;
  const summary = useMemo(
    () => `${daysLabel(workDays)} · ${minutesToLabel(startMin)}–${minutesToLabel(endMin)}`,
    [workDays, startMin, endMin],
  );

  function toggleDay(day: number) {
    setWorkDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort((a, b) => a - b),
    );
  }

  function applyPreset(days: readonly number[]) {
    setWorkDays([...days]);
  }

  function pointerToMinutes(clientX: number): number {
    const track = trackRef.current;
    if (!track) return startMin;
    const rect = track.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    // snap to 15 minutes
    const raw = ratio * 24 * 60;
    return Math.round(raw / 15) * 15;
  }

  function onTrackPointerDown(kind: "start" | "end", event: ReactPointerEvent) {
    event.preventDefault();
    dragKind.current = kind;
    const target = event.currentTarget;
    target.setPointerCapture(event.pointerId);
    const apply = (clientX: number) => {
      const next = pointerToMinutes(clientX);
      if (dragKind.current === "start") {
        setStartMinutes(next);
      } else if (dragKind.current === "end") {
        setEndMinutes(next);
      }
    };
    apply(event.clientX);

    const onMove = (moveEvent: PointerEvent) => apply(moveEvent.clientX);
    const onUp = () => {
      dragKind.current = null;
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  function onTrackClick(event: React.MouseEvent<HTMLDivElement>) {
    if ((event.target as HTMLElement).closest(".schedule-thumb")) return;
    const minutes = pointerToMinutes(event.clientX);
    const distStart = Math.abs(minutes - startMin);
    const distEnd = Math.abs(minutes - endMin);
    if (distStart <= distEnd) {
      setStartMinutes(minutes);
    } else {
      setEndMinutes(minutes);
    }
  }

  function commitStartText() {
    const parsed = parseTimeInput(startText);
    if (!parsed) {
      setStartText(minutesToLabel(startMin));
      return;
    }
    const minutes = labelToMinutes(parsed);
    if (minutes >= endMin) {
      setStartText(minutesToLabel(startMin));
      return;
    }
    setStartMin(minutes);
    setStartText(parsed);
  }

  function commitEndText() {
    const parsed = parseTimeInput(endText);
    if (!parsed) {
      setEndText(minutesToLabel(endMin));
      return;
    }
    const minutes = labelToMinutes(parsed);
    if (minutes <= startMin) {
      setEndText(minutesToLabel(endMin));
      return;
    }
    setEndMin(minutes);
    setEndText(parsed);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    setMessageType("");

    // Apply any in-progress typed times before save
    const startParsed = parseTimeInput(startText);
    const endParsed = parseTimeInput(endText);
    let resolvedStart = startMin;
    let resolvedEnd = endMin;
    if (startParsed) resolvedStart = labelToMinutes(startParsed);
    if (endParsed) resolvedEnd = labelToMinutes(endParsed);
    if (resolvedStart >= resolvedEnd) {
      setMessage("Время окончания должно быть позже начала");
      setMessageType("error");
      return;
    }
    setStartMin(resolvedStart);
    setEndMin(resolvedEnd);
    setStartText(minutesToLabel(resolvedStart));
    setEndText(minutesToLabel(resolvedEnd));

    const number = Number(agentNumber);
    if (!fullName.trim()) {
      setMessage("Укажите ФИО");
      setMessageType("error");
      return;
    }
    if (!Number.isInteger(number) || number < 1) {
      setMessage("Номер агента — целое число от 1");
      setMessageType("error");
      return;
    }
    if (workDays.length === 0) {
      setMessage("Выберите рабочие дни");
      setMessageType("error");
      return;
    }
    if (mode === "create" && !password) {
      setMessage("Задайте пароль");
      setMessageType("error");
      return;
    }

    const payload = {
      full_name: fullName.trim(),
      agent_number: number,
      password: password || undefined,
      work_days: workDays,
      work_time_start: minutesToLabel(resolvedStart),
      work_time_end: minutesToLabel(resolvedEnd),
    };

    setLoading(true);
    try {
      if (mode === "create") {
        await createAgent({
          full_name: payload.full_name,
          agent_number: payload.agent_number,
          password: password,
          work_days: payload.work_days,
          work_time_start: payload.work_time_start,
          work_time_end: payload.work_time_end,
        });
      } else if (agent) {
        await updateAgent(agent.user_account_id, {
          full_name: payload.full_name,
          agent_number: payload.agent_number,
          password: password || undefined,
          work_days: payload.work_days,
          work_time_start: payload.work_time_start,
          work_time_end: payload.work_time_end,
        });
      }
      onSaved();
      onClose();
    } catch (error) {
      setMessageType("error");
      setMessage(error instanceof ApiError ? error.detail : "Не удалось сохранить");
    } finally {
      setLoading(false);
    }
  }

  async function onDelete() {
    if (!agent) return;
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      await deleteAgent(agent.user_account_id);
      onSaved();
      onClose();
    } catch (error) {
      setMessageType("error");
      setMessage(error instanceof ApiError ? error.detail : "Не удалось удалить");
      setConfirmDelete(false);
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  return (
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
            <h2>{mode === "create" ? "Новый агент" : `Агент №${agent?.agent_number ?? ""}`}</h2>
            {mode === "edit" && agent && (
              <span
                className={`status-tag ${
                  agent.is_online ? "status-tag--in_progress" : "status-tag--closed"
                }`}
              >
                {agent.is_online ? "В сети" : "Офлайн"}
              </span>
            )}
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

        <form ref={formRef} className="ticket-detail-body agent-editor-form" onSubmit={onSubmit}>
          <div className="field">
            <label className="field-label" htmlFor="agent-name">
              ФИО<span className="required-mark">*</span>
            </label>
            <input
              id="agent-name"
              className="input-shell"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Денисов Игорь Сергеевич"
              required
            />
          </div>

          <div className="agent-editor-row">
            <div className="field">
              <label className="field-label" htmlFor="agent-number">
                Номер<span className="required-mark">*</span>
              </label>
              <input
                id="agent-number"
                className="input-shell"
                type="number"
                min={1}
                max={9999}
                value={agentNumber}
                onChange={(e) => setAgentNumber(e.target.value)}
                placeholder="1"
                required
              />
            </div>
            <div className="field">
              <label className="field-label" htmlFor="agent-password">
                Пароль{mode === "create" ? <span className="required-mark">*</span> : null}
              </label>
              <input
                id="agent-password"
                className="input-shell"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === "edit" ? "Не менять" : "Минимум 4 символа"}
                autoComplete="new-password"
                required={mode === "create"}
              />
            </div>
          </div>

          <div className="field schedule-field">
            <div className="field-label">График работы<span className="required-mark">*</span></div>
            <div className="schedule-presets">
              {PRESETS.map((preset) => {
                const active =
                  workDays.length === preset.days.length &&
                  preset.days.every((d) => workDays.includes(d));
                return (
                  <button
                    key={preset.id}
                    type="button"
                    className={`schedule-preset${active ? " is-active" : ""}`}
                    onClick={() => applyPreset(preset.days)}
                  >
                    {preset.label}
                  </button>
                );
              })}
            </div>
            <div className="schedule-days" role="group" aria-label="Рабочие дни">
              {WEEKDAYS.map((day) => {
                const active = workDays.includes(day.id);
                return (
                  <button
                    key={day.id}
                    type="button"
                    className={`schedule-day${active ? " is-active" : ""}`}
                    title={day.full}
                    aria-pressed={active}
                    onClick={() => toggleDay(day.id)}
                  >
                    {day.short}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="field schedule-field">
            <div className="field-label">Время работы<span className="required-mark">*</span></div>
            <div className="schedule-time-summary">
              <input
                className="schedule-time-chip"
                type="text"
                inputMode="numeric"
                aria-label="Начало смены"
                value={startText}
                onChange={(e) => setStartText(e.target.value)}
                onBlur={commitStartText}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    (e.target as HTMLInputElement).blur();
                  }
                }}
                placeholder="09:00"
              />
              <span className="schedule-time-sep">→</span>
              <input
                className="schedule-time-chip"
                type="text"
                inputMode="numeric"
                aria-label="Конец смены"
                value={endText}
                onChange={(e) => setEndText(e.target.value)}
                onBlur={commitEndText}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    (e.target as HTMLInputElement).blur();
                  }
                }}
                placeholder="18:00"
              />
              <span className="schedule-duration">
                {Math.max(0, Math.round(((endMin - startMin) / 60) * 10) / 10)} ч
              </span>
            </div>
            <div
              ref={trackRef}
              className="schedule-track"
              onClick={onTrackClick}
              role="slider"
              aria-valuemin={0}
              aria-valuemax={24 * 60}
              aria-label="Диапазон рабочего времени"
            >
              <div className="schedule-track-bg" />
              <div
                className="schedule-track-fill"
                style={{ left: `${startPct}%`, width: `${Math.max(0, endPct - startPct)}%` }}
              />
              <button
                type="button"
                className="schedule-thumb schedule-thumb--start"
                style={{ left: `${startPct}%` }}
                aria-label="Начало смены"
                onPointerDown={(e) => onTrackPointerDown("start", e)}
              />
              <button
                type="button"
                className="schedule-thumb schedule-thumb--end"
                style={{ left: `${endPct}%` }}
                aria-label="Конец смены"
                onPointerDown={(e) => onTrackPointerDown("end", e)}
              />
              <div className="schedule-track-labels">
                <span>00</span>
                <span>06</span>
                <span>12</span>
                <span>18</span>
                <span>24</span>
              </div>
            </div>
          </div>

          <div className="schedule-live-hint">
            Итого: <strong>{summary}</strong>
          </div>

          {message && (
            <p className={`auth-message ${messageType === "error" ? "error" : ""}`}>{message}</p>
          )}

          <div className="ticket-agent-actions-row agent-editor-actions">
            {mode === "edit" && (
              <button
                type="button"
                className={`btn-secondary-ticket${confirmDelete ? " is-danger" : ""}`}
                disabled={loading}
                onClick={() => void onDelete()}
              >
                {confirmDelete ? "Подтвердить удаление" : "Удалить"}
              </button>
            )}
            <button
              type="button"
              className="btn-secondary-ticket"
              disabled={loading}
              onClick={onClose}
            >
              Отменить
            </button>
            <button type="submit" className="btn-submit-ticket" disabled={loading}>
              {loading ? "Сохранение…" : mode === "create" ? "Создать" : "Сохранить"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
