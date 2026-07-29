import type {
  AccessTokenResponse,
  AgentAdmin,
  AgentCreatePayload,
  AgentListResponse,
  AgentUpdatePayload,
  ProblemReasonOption,
  SupportTicket,
  SupportTicketListResponse,
  TicketPoolListResponse,
  TicketStatus,
  UserAccount,
} from "@/types/api";
import { clearAuthSession, getAccessToken } from "@/lib/auth-storage";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

function formatDetail(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "Ошибка запроса";
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) =>
        typeof item === "object" && item && "msg" in item
          ? String((item as { msg: string }).msg)
          : JSON.stringify(item),
      )
      .join("; ");
  }
  return "Ошибка запроса";
}

async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  auth = false,
): Promise<T> {
  const headers = new Headers(init.headers || {});
  if (auth) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      /* empty */
    }
    // Expired / invalid JWT — drop local session so UI can send user to login
    if (response.status === 401 && auth) {
      clearAuthSession();
    }
    throw new ApiError(response.status, formatDetail(payload));
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function loginUser(email: string, password: string): Promise<AccessTokenResponse> {
  return apiFetch<AccessTokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function registerClient(
  email: string,
  fullName: string,
  password: string,
): Promise<AccessTokenResponse> {
  return apiFetch<AccessTokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      full_name: fullName,
      password,
    }),
  });
}

export async function fetchMyUserAccount(): Promise<UserAccount> {
  return apiFetch<UserAccount>("/auth/me", {}, true);
}

export async function logoutUser(): Promise<void> {
  try {
    await apiFetch<UserAccount>("/auth/logout", { method: "POST" }, true);
  } catch {
    /* still clear local session */
  }
}

/** Mark agent offline on server, then wipe local JWT. */
export async function logoutAndClearSession(): Promise<void> {
  await logoutUser();
  clearAuthSession();
}

export async function fetchAdminAgents(): Promise<AgentListResponse> {
  return apiFetch<AgentListResponse>("/admin/agents", {}, true);
}

export async function createAgent(payload: AgentCreatePayload): Promise<AgentAdmin> {
  return apiFetch<AgentAdmin>(
    "/admin/agents",
    { method: "POST", body: JSON.stringify(payload) },
    true,
  );
}

export async function updateAgent(
  userAccountId: number,
  payload: AgentUpdatePayload,
): Promise<AgentAdmin> {
  return apiFetch<AgentAdmin>(
    `/admin/agents/${userAccountId}`,
    { method: "PATCH", body: JSON.stringify(payload) },
    true,
  );
}

export async function deleteAgent(userAccountId: number): Promise<void> {
  await apiFetch<void>(`/admin/agents/${userAccountId}`, { method: "DELETE" }, true);
}

export async function fetchProblemReasons(): Promise<ProblemReasonOption[]> {
  return apiFetch<ProblemReasonOption[]>("/tickets/problem-reasons");
}

export async function fetchMyTickets(): Promise<SupportTicketListResponse> {
  return apiFetch<SupportTicketListResponse>("/tickets/my", {}, true);
}

export async function fetchTicketDetail(ticketId: number): Promise<SupportTicket> {
  return apiFetch<SupportTicket>(`/tickets/${ticketId}`, {}, true);
}

export async function createTicket(
  problemReason: string,
  description: string,
  photos: File[],
): Promise<SupportTicket> {
  const formData = new FormData();
  formData.append("problem_reason", problemReason);
  formData.append("description", description);
  photos.forEach((file) => formData.append("photos", file));
  return apiFetch<SupportTicket>(
    "/tickets",
    {
      method: "POST",
      body: formData,
    },
    true,
  );
}

export async function fetchTicketAttachmentBlob(
  ticketId: number,
  attachmentId: number,
): Promise<Blob> {
  const token = getAccessToken();
  const response = await fetch(
    `${API_BASE_URL}/tickets/${ticketId}/attachments/${attachmentId}/file`,
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  );
  if (!response.ok) {
    throw new ApiError(response.status, "Не удалось загрузить фото");
  }
  return response.blob();
}

export async function fetchTicketPool(
  status?: TicketStatus | null,
): Promise<TicketPoolListResponse> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<TicketPoolListResponse>(`/tickets/pool${query}`, {}, true);
}

export async function fetchTicketArchive(): Promise<TicketPoolListResponse> {
  return apiFetch<TicketPoolListResponse>("/tickets/archive", {}, true);
}

export async function claimTicket(ticketId: number): Promise<SupportTicket> {
  return apiFetch<SupportTicket>(`/tickets/${ticketId}/claim`, { method: "POST" }, true);
}

export async function closeTicket(
  ticketId: number,
  commentText: string,
): Promise<SupportTicket> {
  return apiFetch<SupportTicket>(
    `/tickets/${ticketId}/close`,
    {
      method: "POST",
      body: JSON.stringify({ comment_text: commentText }),
    },
    true,
  );
}

export async function transferTicketToEngineers(ticketId: number): Promise<SupportTicket> {
  return apiFetch<SupportTicket>(
    `/tickets/${ticketId}/transfer-to-engineers`,
    { method: "POST" },
    true,
  );
}

export { API_BASE_URL };
