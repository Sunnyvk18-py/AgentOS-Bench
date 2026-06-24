import { useStats } from "@/hooks/useRuns";
import { formatCost, formatLatency, formatScore } from "@/lib/utils";
import { Activity, Clock, DollarSign, Target } from "lucide-react";

export function StatsCards() {
  const { data, isLoading, isError } = useStats();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="skeleton h-28 rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-xl border border-error/40 bg-error/10 p-4 text-error">
        Failed to load dashboard stats.
      </div>
    );
  }

  const cards = [
    { label: "Total Runs", value: String(data.total_runs), icon: Activity },
    { label: "Avg Composite Score", value: formatScore(data.avg_composite_score), icon: Target },
    { label: "Avg Latency", value: formatLatency(data.avg_latency_ms), icon: Clock },
    { label: "Total Cost", value: formatCost(data.total_cost_usd), icon: DollarSign },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ label, value, icon: Icon }) => (
        <div
          key={label}
          className="card-hover rounded-xl border border-border bg-card p-5"
        >
          <div className="flex items-center justify-between">
            <p className="text-sm text-foreground/60">{label}</p>
            <Icon className="h-4 w-4 text-primary" />
          </div>
          <p className="mt-3 text-2xl font-semibold font-mono">{value}</p>
        </div>
      ))}
    </div>
  );
}
