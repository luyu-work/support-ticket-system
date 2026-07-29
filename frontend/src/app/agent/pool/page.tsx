"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AgentStaffShell } from "@/components/agent/AgentStaffShell";
import { FilterStub } from "@/components/agent/FilterStub";
import {
  sortPoolItems,
  TicketPoolTable,
  type PoolSortKey,
} from "@/components/agent/TicketPoolTable";
import { TicketDetailModal } from "@/components/tickets/TicketDetailModal";
import { useRequireRole } from "@/hooks/useRequireRole";
import { ApiError, claimTicket, fetchTicketDetail, fetchTicketPool } from "@/lib/api";
import { nextSortState, type SortDir } from "@/lib/sort";
import type { PoolTicketItem, SupportTicket } from "@/types/api";

export default function AgentPoolPage() {
  const user = useRequireRole("agent");
  const [items, setItems] = useState<PoolTicketItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sortKey, setSortKey] = useState<PoolSortKey>("id");
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
    if (user) void loadPool();
  }, [user, loadPool]);

  const sortedItems = useMemo(
    () => sortPoolItems(items, sortKey, sortDir),
    [items, sortKey, sortDir],
  );

  function toggleSort(key: PoolSortKey) {
    const next = nextSortState(sortKey, sortDir, key, "asc");
    setSortKey(next.key);
    setSortDir(next.dir);
  }

  async function openRow(item: PoolTicketItem) {
    setActionMessage("");
    const needsResolution =
      item.status === "in_queue" || item.status === "important";

    try {
      if (!item.assigned_agent && needsResolution) {
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
          <FilterStub />
        </div>

        {actionMessage && <p className="agent-empty">{actionMessage}</p>}

        <div className="agent-table-wrap">
          {loading && <p className="agent-empty">Загрузка…</p>}
          {!loading && error && <p className="agent-empty">{error}</p>}
          {!loading && !error && sortedItems.length === 0 && (
            <p className="agent-empty">В пуле пока нет тикетов</p>
          )}
          {!loading && !error && sortedItems.length > 0 && (
            <TicketPoolTable
              items={sortedItems}
              sortKey={sortKey}
              sortDir={sortDir}
              onSort={toggleSort}
              onRowClick={(item) => void openRow(item)}
              highlightImportant
            />
          )}
        </div>
      </section>

      <TicketDetailModal
        ticket={selectedTicket}
        open={Boolean(selectedTicket)}
        lockUntilResolved={lockUntilResolved}
        agentActions
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
