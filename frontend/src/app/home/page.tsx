"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, getPostLoginPath, getStoredUserAccount } from "@/lib/auth-storage";

/**
 * Legacy route: send authenticated users to their role home, others to login.
 */
export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = getAccessToken();
    const account = getStoredUserAccount();
    if (!token || !account) {
      router.replace("/login");
      return;
    }
    router.replace(getPostLoginPath(account));
  }, [router]);

  return null;
}
