import type { TicketStatus } from "@/types/api";

export const STATUS_LABELS_RU: Record<TicketStatus, string> = {
  in_queue: "В очереди",
  important: "Важное",
  in_progress: "В работе",
  closed: "Закрыт",
  transferred_to_engineers: "Передан инженерам",
};

export const PROBLEM_REASON_LABELS_RU: Record<string, string> = {
  bug_report: "Баги",
  payment_issue: "Проблема с оплатой",
  feature_request: "Предложения по улучшению",
  login_issue: "Проблема со входом",
  other: "Другое",
};

export const MAX_TICKET_PHOTOS = 5;

export function getCategoryLabel(problemReason: string): string {
  return PROBLEM_REASON_LABELS_RU[problemReason] || problemReason;
}

export function getStatusLabel(status: TicketStatus | string): string {
  return STATUS_LABELS_RU[status as TicketStatus] || status;
}

export function getFirstLetter(fullName: string): string {
  const trimmed = fullName.trim();
  return trimmed ? trimmed[0].toUpperCase() : "?";
}
