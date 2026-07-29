type SortDir = "asc" | "desc";

/** Dual chevron: inactive = both gray; active asc = up blue; active desc = down blue. */
export function SortChevrons({ active, dir }: { active: boolean; dir: SortDir }) {
  const up = active && dir === "asc" ? "#3761F3" : "#9A9A9A";
  const down = active && dir === "desc" ? "#3761F3" : "#9A9A9A";
  return (
    <span className="agent-sort-chevrons" aria-hidden>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path
          d="M11 10L8 13L5 10H11Z"
          fill={down}
          stroke={down}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M5 6L8 3L11 6L5 6Z"
          fill={up}
          stroke={up}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}
