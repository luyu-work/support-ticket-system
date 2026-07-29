"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clearAuthSession, getAccessToken, getStoredUserAccount } from "@/lib/auth-storage";
import type { UserAccount } from "@/types/api";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserAccount | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    const account = getStoredUserAccount();
    if (!token || !account) {
      router.replace("/login");
      return;
    }
    if (account.role === "client") {
      router.replace("/tickets");
      return;
    }
    if (account.role === "agent" || account.role === "admin") {
      router.replace("/agent/pool");
      return;
    }
    setUser(account);
  }, [router]);

  if (!user) return null;

  return (
    <main className="home-card">
      <h1 className="auth-title">Вы вошли в систему</h1>
      <p className="auth-subtitle">
        Для клиента форма тикета: <a href="/tickets">/tickets</a>. Пул агента и dashboard
        админа — следующие шаги.
      </p>
      <p className="home-meta">
        <strong>{user.full_name}</strong>
        <br />
        Роль: <strong>{user.role}</strong>
        <br />
        Почта: <strong>{user.email}</strong>
      </p>
      <div className="btn-row">
        <button
          type="button"
          className="btn-secondary"
          onClick={() => {
            clearAuthSession();
            router.push("/login");
          }}
        >
          Выйти
        </button>
      </div>
    </main>
  );
}
