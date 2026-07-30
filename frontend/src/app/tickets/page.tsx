"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CreateTicketModal } from "@/components/tickets/CreateTicketModal";
import { TicketCard } from "@/components/tickets/TicketCard";
import { TicketDetailModal } from "@/components/tickets/TicketDetailModal";
import { fetchMyTickets } from "@/lib/api";
import {
  clearAuthSession,
  getAccessToken,
  getPostLoginPath,
  getStoredUserAccount,
} from "@/lib/auth-storage";
import { getFirstLetter } from "@/lib/labels";
import type { SupportTicket, UserAccount } from "@/types/api";

export default function TicketsPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserAccount | null>(null);
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setListError("");
    try {
      const payload = await fetchMyTickets();
      setTickets(payload.items);
    } catch {
      setListError("Не удалось загрузить тикеты");
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = getAccessToken();
    const account = getStoredUserAccount();
    if (!token || !account) {
      router.replace("/login");
      return;
    }
    if (account.role !== "client") {
      router.replace(getPostLoginPath(account));
      return;
    }
    setUser(account);
    void loadTickets();
  }, [router, loadTickets]);

  if (!user) return null;

  return (
    <div className="client-shell tickets-page-root" style={{ height: "100vh", boxSizing: "border-box" }}>
      <header className="client-profile-card">
        <div className="client-profile">
          <div className="client-avatar" aria-hidden>
            {getFirstLetter(user.full_name)}
          </div>
          <div className="client-profile-text">
            <div className="client-profile-name">{user.full_name}</div>
            <div className="client-profile-role">Клиент</div>
          </div>
        </div>
        <button
          type="button"
          className="icon-button"
          aria-label="Выйти"
          title="Выйти"
          onClick={() => {
            clearAuthSession();
            router.push("/login");
          }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
            <path
              d="M8.00001 6.00008L10 8.00008L8.00001 10.0001M10 8.00008H2.66667M6.00001 4.83247V4.80021C6.00001 4.05347 6.00001 3.67983 6.14533 3.39461C6.27316 3.14373 6.47699 2.9399 6.72787 2.81207C7.01309 2.66675 7.38673 2.66675 8.13347 2.66675H11.2001C11.9469 2.66675 12.3197 2.66675 12.6049 2.81207C12.8558 2.9399 13.0603 3.14373 13.1882 3.39461C13.3333 3.67955 13.3333 4.05274 13.3333 4.79802V11.2025C13.3333 11.9477 13.3333 12.3204 13.1882 12.6053C13.0603 12.8562 12.8558 13.0604 12.6049 13.1882C12.32 13.3334 11.9473 13.3334 11.2021 13.3334H8.13128C7.386 13.3334 7.01281 13.3334 6.72787 13.1882C6.47699 13.0604 6.27316 12.856 6.14533 12.6051C6.00001 12.3199 6.00001 11.9468 6.00001 11.2001V11.1667"
              stroke="#333333"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </header>

      <section className="client-main-card">
        <div className="client-main-title">
          <h1>Мои тикеты</h1>
          <button type="button" className="btn-feedback" onClick={() => setCreateOpen(true)}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
              <path
                d="M4 8H8M8 8H12M8 8V12M8 8V4"
                stroke="#F1F5FF"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span>Обратная связь</span>
          </button>
        </div>

        <div className="client-ticket-list">
          {loading && <p className="muted-text">Загрузка…</p>}
          {!loading && listError && <p className="muted-text">{listError}</p>}
          {!loading && !listError && tickets.length === 0 && (
            <p className="muted-text">
              Пока нет тикетов. Нажмите «Обратная связь», чтобы создать первый.
            </p>
          )}
          {!loading &&
            tickets.map((ticket) => (
              <TicketCard key={ticket.support_ticket_id} ticket={ticket} onOpen={setSelectedTicket} />
            ))}
        </div>
      </section>

      <CreateTicketModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => void loadTickets()}
      />
      <TicketDetailModal
        ticket={selectedTicket}
        open={Boolean(selectedTicket)}
        onClose={() => setSelectedTicket(null)}
      />
    </div>
  );
}
