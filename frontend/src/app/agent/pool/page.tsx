"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AgentStaffShell } from "@/components/agent/AgentStaffShell";
import { SortChevrons } from "@/components/agent/SortChevrons";
import { TicketDetailModal } from "@/components/tickets/TicketDetailModal";
import { ApiError, claimTicket, fetchTicketDetail, fetchTicketPool } from "@/lib/api";
import {
  formatTicketCreatedAt,
  getAccessToken,
  getStoredUserAccount,
} from "@/lib/auth-storage";
import { getStatusLabel } from "@/lib/labels";
import type { PoolTicketItem, SupportTicket, UserAccount } from "@/types/api";

type SortKey = "id" | "status" | "created_at" | "assignee";
type SortDir = "asc" | "desc";

export default function AgentPoolPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserAccount | null>(null);
  const [items, setItems] = useState<PoolTicketItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>("id");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [lockUntilResolved, setLockUntilResolved] = useState(false);
  const [actionMessage, setActionMessage] = useState("");

  const loadPool = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchTicketPool();
      setItems(payload.items);
    } catch {
      setError("Не удалось загрузить пул тикетов");
      setItems([]);
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
    if (account.role === "admin") {
      router.replace("/agent/agents");
      return;
    }
    if (account.role !== "agent") {
      router.replace(account.role === "client" ? "/tickets" : "/home");
      return;
    }
    setUser(account);
  }, [router]);

  useEffect(() => {
    if (user) void loadPool();
  }, [user, loadPool]);

  const sortedItems = useMemo(() => {
    const copy = [...items];
    copy.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "id") {
        cmp = a.support_ticket_id - b.support_ticket_id;
      } else if (sortKey === "status") {
        cmp = a.status.localeCompare(b.status);
      } else if (sortKey === "created_at") {
        cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else {
        const an = a.assigned_agent?.full_name || "";
        const bn = b.assigned_agent?.full_name || "";
        cmp = an.localeCompare(bn, "ru");
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [items, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  async function openRow(item: PoolTicketItem) {
    setActionMessage("");
    const needsResolution =
      user?.role === "agent" &&
      (item.status === "in_queue" || item.status === "important");

    try {
      // Free agent claims unassigned pool tickets when opening them
      if (
        user?.role === "agent" &&
        !item.assigned_agent &&
        (item.status === "in_queue" || item.status === "important")
      ) {
        await claimTicket(item.support_ticket_id);
        await loadPool();
      }
      const detail = await fetchTicketDetail(item.support_ticket_id);
      setLockUntilResolved(needsResolution);
      setSelectedTicket(detail);
    } catch (err) {
      setActionMessage(
        err instanceof ApiError ? err.detail : "Не удалось открыть тикет",
      );
    }
  }

  if (!user) return null;

  return (
    <AgentStaffShell user={user} activeNav="pool">
      <section className="agent-main-card">
        <div className="agent-main-title">
          <h1>Пул тикетов</h1>
          <div className="agent-filter-wrap">
            <button
              type="button"
              className={`agent-filter-button${filterOpen ? " is-open" : ""}`}
              onClick={() => setFilterOpen((v) => !v)}
              aria-expanded={filterOpen}
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                <path
                  d="M13.3334 3.73348C13.3334 3.36011 13.3331 3.17329 13.2604 3.03068C13.1965 2.90524 13.0949 2.80333 12.9695 2.73941C12.8269 2.66675 12.6398 2.66675 12.2664 2.66675H3.73309C3.35972 2.66675 3.17323 2.66675 3.03062 2.73941C2.90518 2.80333 2.80326 2.90524 2.73935 3.03068C2.66669 3.17329 2.66669 3.36011 2.66669 3.73348V4.22499C2.66669 4.38805 2.66669 4.46964 2.68511 4.54636C2.70144 4.61439 2.72844 4.67937 2.76499 4.73901C2.80621 4.80627 2.86396 4.86402 2.97919 4.97925L6.35435 8.35441C6.46964 8.4697 6.52698 8.52704 6.56821 8.59432C6.60476 8.65396 6.63213 8.71917 6.64846 8.78719C6.66669 8.86313 6.66669 8.94376 6.66669 9.10352V12.2741C6.66669 12.8456 6.66669 13.1315 6.78705 13.3036C6.89215 13.4538 7.05429 13.5541 7.2357 13.5809C7.44345 13.6116 7.69916 13.4839 8.21031 13.2283L8.74364 12.9617C8.95768 12.8547 9.06444 12.8009 9.14263 12.7211C9.21178 12.6505 9.26467 12.5657 9.2969 12.4723C9.33333 12.3667 9.33335 12.2467 9.33335 12.0074V9.10848C9.33335 8.94542 9.33335 8.86392 9.35177 8.78719C9.36811 8.71917 9.39511 8.65396 9.43166 8.59432C9.47261 8.52749 9.5298 8.4703 9.64356 8.35654L9.64585 8.35441L13.021 4.97925C13.1363 4.86395 13.1936 4.80629 13.2349 4.73901C13.2714 4.67937 13.2988 4.61439 13.3151 4.54636C13.3334 4.47042 13.3334 4.38971 13.3334 4.22995V3.73348Z"
                  stroke="#333333"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span>Фильтр</span>
            </button>
            {filterOpen && (
              <div className="agent-filter-dropdown" role="dialog" aria-label="Фильтр">
                <p className="agent-filter-stub">Фильтры скоро появятся</p>
              </div>
            )}
          </div>
        </div>

        {actionMessage && <p className="agent-empty">{actionMessage}</p>}

        <div className="agent-table-wrap">
          {loading && <p className="agent-empty">Загрузка…</p>}
          {!loading && error && <p className="agent-empty">{error}</p>}
          {!loading && !error && sortedItems.length === 0 && (
            <p className="agent-empty">В пуле пока нет тикетов</p>
          )}
          {!loading && !error && sortedItems.length > 0 && (
            <table className="agent-table">
              <thead>
                <tr>
                  <th className="col-id">
                    <button
                      type="button"
                      className={`agent-sort-button${sortKey === "id" ? " is-active" : ""}`}
                      onClick={() => toggleSort("id")}
                      aria-sort={
                        sortKey === "id"
                          ? sortDir === "asc"
                            ? "ascending"
                            : "descending"
                          : "none"
                      }
                    >
                      <span>ID тикета</span>
                      <SortChevrons active={sortKey === "id"} dir={sortDir} />
                    </button>
                  </th>
                  <th className="col-status">
                    <button
                      type="button"
                      className={`agent-sort-button${sortKey === "status" ? " is-active" : ""}`}
                      onClick={() => toggleSort("status")}
                      aria-sort={
                        sortKey === "status"
                          ? sortDir === "asc"
                            ? "ascending"
                            : "descending"
                          : "none"
                      }
                    >
                      <span>Статус</span>
                      <SortChevrons active={sortKey === "status"} dir={sortDir} />
                    </button>
                  </th>
                  <th className="col-time">
                    <button
                      type="button"
                      className={`agent-sort-button${
                        sortKey === "created_at" ? " is-active" : ""
                      }`}
                      onClick={() => toggleSort("created_at")}
                      aria-sort={
                        sortKey === "created_at"
                          ? sortDir === "asc"
                            ? "ascending"
                            : "descending"
                          : "none"
                      }
                    >
                      <span>Время создания</span>
                      <SortChevrons active={sortKey === "created_at"} dir={sortDir} />
                    </button>
                  </th>
                  <th className="col-reason">Причина</th>
                  <th>
                    <button
                      type="button"
                      className={`agent-sort-button${
                        sortKey === "assignee" ? " is-active" : ""
                      }`}
                      onClick={() => toggleSort("assignee")}
                      aria-sort={
                        sortKey === "assignee"
                          ? sortDir === "asc"
                            ? "ascending"
                            : "descending"
                          : "none"
                      }
                    >
                      <span>Ответственный</span>
                      <SortChevrons active={sortKey === "assignee"} dir={sortDir} />
                    </button>
                  </th>
                  <th className="col-arrow" />
                </tr>
              </thead>
              <tbody>
                {sortedItems.map((item) => (
                  <tr key={item.support_ticket_id} onClick={() => void openRow(item)}>
                    <td className="agent-id-cell">№{item.support_ticket_id}</td>
                    <td>
                      <span className={`status-tag status-tag--${item.status}`}>
                        {getStatusLabel(item.status)}
                      </span>
                    </td>
                    <td
                      className={`agent-time-cell${
                        item.status === "important" ? " is-important" : ""
                      }`}
                    >
                      {formatTicketCreatedAt(item.created_at)}
                    </td>
                    <td>{item.problem_reason_label}</td>
                    <td>
                      {item.assigned_agent ? (
                        <>
                          <div className="agent-assignee-name">{item.assigned_agent.full_name}</div>
                          <div className="agent-assignee-badge">
                            {item.assigned_agent.agent_badge}
                          </div>
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="col-arrow">
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                        <path
                          d="M6 3.33325L10.6667 7.99992L6 12.6666"
                          stroke="#333333"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      <TicketDetailModal
        ticket={selectedTicket}
        open={Boolean(selectedTicket)}
        lockUntilResolved={lockUntilResolved}
        agentActions={user.role === "agent"}
        showTicketLogs
        onResolved={() => {
          setLockUntilResolved(false);
          setSelectedTicket(null);
          void loadPool();
        }}
        onClose={() => {
          setSelectedTicket(null);
          setLockUntilResolved(false);
          void loadPool();
        }}
      />
    </AgentStaffShell>
  );
}
