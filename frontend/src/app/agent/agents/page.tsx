"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AgentEditorModal } from "@/components/agent/AgentEditorModal";
import { AgentStaffShell } from "@/components/agent/AgentStaffShell";
import { SortChevrons } from "@/components/agent/SortChevrons";
import { fetchAdminAgents } from "@/lib/api";
import { getAccessToken, getStoredUserAccount } from "@/lib/auth-storage";
import type { AgentAdmin, UserAccount } from "@/types/api";

type SortKey = "number" | "name" | "schedule" | "time" | "online";
type SortDir = "asc" | "desc";

export default function AdminAgentsPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserAccount | null>(null);
  const [items, setItems] = useState<AgentAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("number");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selected, setSelected] = useState<AgentAdmin | null>(null);

  const loadAgents = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchAdminAgents();
      setItems(payload.items);
    } catch {
      setError("Не удалось загрузить список агентов");
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
    if (account.role !== "admin") {
      if (account.role === "agent") router.replace("/agent/pool");
      else if (account.role === "client") router.replace("/tickets");
      else router.replace("/home");
      return;
    }
    setUser(account);
  }, [router]);

  useEffect(() => {
    if (user) void loadAgents();
  }, [user, loadAgents]);

  const sorted = useMemo(() => {
    const copy = [...items];
    copy.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "number") {
        cmp = (a.agent_number ?? 99999) - (b.agent_number ?? 99999);
      } else if (sortKey === "name") {
        cmp = a.full_name.localeCompare(b.full_name, "ru");
      } else if (sortKey === "schedule") {
        cmp = a.work_days_label.localeCompare(b.work_days_label, "ru");
      } else if (sortKey === "time") {
        cmp = (a.work_time_label || "").localeCompare(b.work_time_label || "", "ru");
      } else {
        cmp = Number(b.is_online) - Number(a.is_online);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [items, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function openCreate() {
    setSelected(null);
    setModalMode("create");
    setModalOpen(true);
  }

  function openEdit(agent: AgentAdmin) {
    setSelected(agent);
    setModalMode("edit");
    setModalOpen(true);
  }

  if (!user) return null;

  return (
    <AgentStaffShell user={user} activeNav="agents">
      <section className="agent-main-card">
        <div className="agent-main-title">
          <h1>Агенты</h1>
          <button type="button" className="btn-submit-ticket agents-add-button" onClick={openCreate}>
            Добавить агента
          </button>
        </div>

        <div className="agent-table-wrap">
          {loading && <p className="agent-empty">Загрузка…</p>}
          {!loading && error && <p className="agent-empty">{error}</p>}
          {!loading && !error && sorted.length === 0 && (
            <p className="agent-empty">Агентов пока нет. Добавьте первого.</p>
          )}
          {!loading && !error && sorted.length > 0 && (
            <table className="agent-table">
              <thead>
                <tr>
                  <th className="col-agent-num">
                    <button
                      type="button"
                      className={`agent-sort-button${sortKey === "number" ? " is-active" : ""}`}
                      onClick={() => toggleSort("number")}
                    >
                      <span>№</span>
                      <SortChevrons active={sortKey === "number"} dir={sortDir} />
                    </button>
                  </th>
                  <th>
                    <button
                      type="button"
                      className={`agent-sort-button${sortKey === "name" ? " is-active" : ""}`}
                      onClick={() => toggleSort("name")}
                    >
                      <span>ФИО</span>
                      <SortChevrons active={sortKey === "name"} dir={sortDir} />
                    </button>
                  </th>
                  <th>
                    <button
                      type="button"
                      className={`agent-sort-button${sortKey === "schedule" ? " is-active" : ""}`}
                      onClick={() => toggleSort("schedule")}
                    >
                      <span>График</span>
                      <SortChevrons active={sortKey === "schedule"} dir={sortDir} />
                    </button>
                  </th>
                  <th className="col-time">
                    <button
                      type="button"
                      className={`agent-sort-button${sortKey === "time" ? " is-active" : ""}`}
                      onClick={() => toggleSort("time")}
                    >
                      <span>Время</span>
                      <SortChevrons active={sortKey === "time"} dir={sortDir} />
                    </button>
                  </th>
                  <th className="col-status">
                    <button
                      type="button"
                      className={`agent-sort-button${sortKey === "online" ? " is-active" : ""}`}
                      onClick={() => toggleSort("online")}
                    >
                      <span>Статус</span>
                      <SortChevrons active={sortKey === "online"} dir={sortDir} />
                    </button>
                  </th>
                  <th className="col-arrow" />
                </tr>
              </thead>
              <tbody>
                {sorted.map((agent) => (
                  <tr key={agent.user_account_id} onClick={() => openEdit(agent)}>
                    <td className="col-agent-num">
                      {agent.agent_number != null ? agent.agent_number : "—"}
                    </td>
                    <td>{agent.full_name}</td>
                    <td>{agent.work_days_label}</td>
                    <td className="agent-time-cell">{agent.work_time_label}</td>
                    <td>
                      <span
                        className={`status-tag ${
                          agent.is_online ? "status-tag--in_progress" : "status-tag--closed"
                        }`}
                      >
                        {agent.is_online ? "В сети" : "Офлайн"}
                      </span>
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

      <AgentEditorModal
        open={modalOpen}
        mode={modalMode}
        agent={selected}
        onClose={() => setModalOpen(false)}
        onSaved={() => void loadAgents()}
      />
    </AgentStaffShell>
  );
}
