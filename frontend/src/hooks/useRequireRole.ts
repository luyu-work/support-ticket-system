"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, getPostLoginPath, getStoredUserAccount } from "@/lib/auth-storage";
import type { UserAccount, UserRole } from "@/types/api";

/**
 * Gate a page by role. Returns user when allowed, null while redirecting.
 */
export function useRequireRole(allowed: UserRole | UserRole[]): UserAccount | null {
  const router = useRouter();
  const [user, setUser] = useState<UserAccount | null>(null);
  const allowedKey = useMemo(
    () => (Array.isArray(allowed) ? allowed : [allowed]).join("|"),
    [allowed],
  );

  useEffect(() => {
    const allowedList = allowedKey.split("|") as UserRole[];
    const token = getAccessToken();
    const account = getStoredUserAccount();
    if (!token || !account) {
      router.replace("/login");
      return;
    }
    if (!allowedList.includes(account.role)) {
      router.replace(getPostLoginPath(account));
      return;
    }
    setUser(account);
  }, [router, allowedKey]);

  return user;
}
