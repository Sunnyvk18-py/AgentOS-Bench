import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return `${(score * 100).toFixed(1)}%`;
}

export function scoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return "text-foreground/60";
  if (score > 0.8) return "text-success";
  if (score >= 0.5) return "text-warning";
  return "text-error";
}

export function scoreBg(score: number | null | undefined): string {
  if (score === null || score === undefined) return "bg-border";
  if (score > 0.8) return "bg-success";
  if (score >= 0.5) return "bg-warning";
  return "bg-error";
}

export function truncateId(id: string): string {
  return id.slice(0, 8);
}

export function formatLatency(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function formatCost(usd: number | null | undefined): string {
  if (usd === null || usd === undefined) return "—";
  return `$${usd.toFixed(4)}`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function exportCsv(rows: Record<string, string | number | null>[], filename: string) {
  if (!rows.length) return;
  const headers = Object.keys(rows[0]);
  const csv = [
    headers.join(","),
    ...rows.map((row) =>
      headers.map((h) => `"${String(row[h] ?? "").replace(/"/g, '""')}"`).join(",")
    ),
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
