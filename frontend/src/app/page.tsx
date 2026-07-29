"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, getPostLoginPath, getStoredUserAccount } from "@/lib/auth-storage";

export default function HomeRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getAccessToken();
    const user = getStoredUserAccount();
    if (token && user) {
      router.replace(getPostLoginPath(user));
    } else {
      router.replace("/login");
    }
  }, [router]);

  return null;
}
