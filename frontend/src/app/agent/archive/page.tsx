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
import { ApiError, fetchTicketArchive, fetchTicketDetail } from "@/lib/api";
import { nextSortState, type SortDir } from "@/lib/sort";
import type { PoolTicketItem, SupportTicket } from "@/types/api";

export default function AgentArchivePage() {
  const user = useRequireRole("agent");
  const [items, setItems] = useState<PoolTicketItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sortKey, setSortKey] = useState<PoolSortKey>("id");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [actionMessage, setActionMessage] = useState("");

  const loadArchive = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchTicketArchive();
      setItems(payload.items);
    } catch {
      setError("Не удалось загрузить архив");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) void loadArchive();
  }, [user, loadArchive]);

  const sortedItems = useMemo(
    () => sortPoolItems(items, sortKey, sortDir),
    [items, sortKey, sortDir],
  );

  function toggleSort(key: PoolSortKey) {
    const next = nextSortState(sortKey, sortDir, key, "desc");
    setSortKey(next.key);
    setSortDir(next.dir);
  }

  async function openRow(item: PoolTicketItem) {
    setActionMessage("");
    try {
      const detail = await fetchTicketDetail(item.support_ticket_id);
      setSelectedTicket(detail);
    } catch (err) {
      setActionMessage(
        err instanceof ApiError ? err.detail : "Не удалось открыть тикет",
      );
    }
  }

  if (!user) return null;

  return (
    <AgentStaffShell user={user} activeNav="archive">
      <section className="agent-main-card">
        <div className="agent-main-title">
          <h1>Архив</h1>
          <FilterStub />
        </div>

        {actionMessage && <p className="agent-empty">{actionMessage}</p>}

        <div className="agent-table-wrap">
          {loading && <p className="agent-empty">Загрузка…</p>}
          {!loading && error && <p className="agent-empty">{error}</p>}
          {!loading && !error && sortedItems.length === 0 && (
            <p className="agent-empty">В архиве пока нет закрытых тикетов</p>
          )}
          {!loading && !error && sortedItems.length > 0 && (
            <TicketPoolTable
              items={sortedItems}
              sortKey={sortKey}
              sortDir={sortDir}
              onSort={toggleSort}
              onRowClick={(item) => void openRow(item)}
            />
          )}
        </div>
      </section>

      <TicketDetailModal
        ticket={selectedTicket}
        open={Boolean(selectedTicket)}
        agentActions={false}
        showTicketLogs
        onClose={() => setSelectedTicket(null)}
      />
    </AgentStaffShell>
  );
}
