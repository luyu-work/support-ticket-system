export type SortDir = "asc" | "desc";

export function nextSortState<K extends string>(
  currentKey: K,
  currentDir: SortDir,
  nextKey: K,
  defaultDir: SortDir = "asc",
): { key: K; dir: SortDir } {
  if (currentKey === nextKey) {
    return { key: currentKey, dir: currentDir === "asc" ? "desc" : "asc" };
  }
  return { key: nextKey, dir: defaultDir };
}

export function compareStrings(a: string, b: string, locale = "ru"): number {
  return a.localeCompare(b, locale);
}

export function compareNumbers(a: number, b: number): number {
  return a - b;
}

export function applyDir(cmp: number, dir: SortDir): number {
  return dir === "asc" ? cmp : -cmp;
}
