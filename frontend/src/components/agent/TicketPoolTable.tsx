"use client";

import { SortChevrons } from "@/components/agent/SortChevrons";
import { formatTicketCreatedAt } from "@/lib/auth-storage";
import { getStatusLabel } from "@/lib/labels";
import { applyDir, compareNumbers, compareStrings, type SortDir } from "@/lib/sort";
import type { PoolTicketItem } from "@/types/api";

export type PoolSortKey = "id" | "status" | "created_at" | "assignee";

interface TicketPoolTableProps {
  items: PoolTicketItem[];
  sortKey: PoolSortKey;
  sortDir: SortDir;
  onSort: (key: PoolSortKey) => void;
  onRowClick: (item: PoolTicketItem) => void;
  /** Highlight important tickets in time column (pool only). */
  highlightImportant?: boolean;
}

export function sortPoolItems(
  items: PoolTicketItem[],
  sortKey: PoolSortKey,
  sortDir: SortDir,
): PoolTicketItem[] {
  return [...items].sort((a, b) => {
    let cmp = 0;
    if (sortKey === "id") {
      cmp = compareNumbers(a.support_ticket_id, b.support_ticket_id);
    } else if (sortKey === "status") {
      cmp = compareStrings(a.status, b.status, "en");
    } else if (sortKey === "created_at") {
      cmp = compareNumbers(new Date(a.created_at).getTime(), new Date(b.created_at).getTime());
    } else {
      cmp = compareStrings(a.assigned_agent?.full_name || "", b.assigned_agent?.full_name || "");
    }
    return applyDir(cmp, sortDir);
  });
}

function SortHeader({
  label,
  column,
  sortKey,
  sortDir,
  onSort,
  className,
}: {
  label: string;
  column: PoolSortKey;
  sortKey: PoolSortKey;
  sortDir: SortDir;
  onSort: (key: PoolSortKey) => void;
  className?: string;
}) {
  const active = sortKey === column;
  return (
    <th className={className}>
      <button
        type="button"
        className={`agent-sort-button${active ? " is-active" : ""}`}
        onClick={() => onSort(column)}
        aria-sort={active ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
      >
        <span>{label}</span>
        <SortChevrons active={active} dir={sortDir} />
      </button>
    </th>
  );
}

export function TicketPoolTable({
  items,
  sortKey,
  sortDir,
  onSort,
  onRowClick,
  highlightImportant = false,
}: TicketPoolTableProps) {
  return (
    <table className="agent-table">
      <thead>
        <tr>
          <SortHeader
            label="ID тикета"
            column="id"
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={onSort}
            className="col-id"
          />
          <SortHeader
            label="Статус"
            column="status"
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={onSort}
            className="col-status"
          />
          <SortHeader
            label="Время создания"
            column="created_at"
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={onSort}
            className="col-time"
          />
          <th className="col-reason">Причина</th>
          <SortHeader
            label="Ответственный"
            column="assignee"
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={onSort}
          />
          <th className="col-arrow" />
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.support_ticket_id} onClick={() => onRowClick(item)}>
            <td className="agent-id-cell">№{item.support_ticket_id}</td>
            <td>
              <span className={`status-tag status-tag--${item.status}`}>
                {getStatusLabel(item.status)}
              </span>
            </td>
            <td
              className={`agent-time-cell${
                highlightImportant && item.status === "important" ? " is-important" : ""
              }`}
            >
              {formatTicketCreatedAt(item.created_at)}
            </td>
            <td>{item.problem_reason_label}</td>
            <td>
              {item.assigned_agent ? (
                <>
                  <div className="agent-assignee-name">{item.assigned_agent.full_name}</div>
                  <div className="agent-assignee-badge">{item.assigned_agent.agent_badge}</div>
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
  );
}
