"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  clearAuthSession,
  getAccessToken,
  getPostLoginPath,
  getStoredUserAccount,
} from "@/lib/auth-storage";

/**
 * Entry route: send the user to their role home or to login.
 * Renders a minimal placeholder so the shell does not flash empty during replace.
 */
export default function HomeRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getAccessToken();
    const user = getStoredUserAccount();

    if (token && user) {
      router.replace(getPostLoginPath(user));
      return;
    }

    // Half-broken session (token without user, or user without token)
    if (token || user) {
      clearAuthSession();
    }
    router.replace("/login");
  }, [router]);

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        fontFamily: "system-ui, sans-serif",
        color: "#555",
      }}
    >
      Загрузка…
    </main>
  );
}
