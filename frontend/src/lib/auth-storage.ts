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
  return userAccount.role === "client" ? "/tickets" : "/home";
}
