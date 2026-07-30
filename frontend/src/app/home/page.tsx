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
 * Legacy route: same as "/", kept for old bookmarks/links.
 */
export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = getAccessToken();
    const account = getStoredUserAccount();
    if (token && account) {
      router.replace(getPostLoginPath(account));
      return;
    }
    if (token || account) {
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
