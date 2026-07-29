import type { UserAccount } from "@/types/api";

const ACCESS_TOKEN_KEY = "ticket_system_access_token";
const USER_ACCOUNT_KEY = "ticket_system_user_account";

export function saveAuthSession(accessToken: string, userAccount: UserAccount): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(USER_ACCOUNT_KEY, JSON.stringify(userAccount));
}

export function clearAuthSession(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(USER_ACCOUNT_KEY);
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredUserAccount(): UserAccount | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_ACCOUNT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserAccount;
  } catch {
    return null;
  }
}

export function getPostLoginPath(userAccount: UserAccount): string {
  if (userAccount.role === "client") return "/tickets";
  if (userAccount.role === "agent") return "/agent/pool";
  return "/home";
}

export function formatAgentBadge(userAccountId: number): string {
  return `Агент #${String(userAccountId).padStart(3, "0")}`;
}

export function formatTicketCreatedAt(isoDate: string): string {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return isoDate;
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${day}.${month}.${year} ${hours}:${minutes}`;
}
