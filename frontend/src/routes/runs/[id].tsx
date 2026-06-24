import { useParams } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { TraceTimeline } from "@/components/trace/TraceTimeline";
import { RunStatusBadge } from "@/components/runs/RunStatusBadge";
import { useRun } from "@/hooks/useRuns";
import { useExportReport } from "@/hooks/useReports";
import {
  formatCost,
  formatDate,
  formatLatency,
  formatScore,
  scoreBg,
  scoreColor,
  truncateId,
} from "@/lib/utils";
import { Download } from "lucide-react";

export default function RunDetailPage() {
  const { id = "" } = useParams();
  const { data: run, isLoading, isError } = useRun(id);
  const exportReport = useExportReport();

  const handleExport = async (format: "json" | "markdown") => {
    const result = await exportReport.mutateAsync({ runId: id, format });
    const content = typeof result === "string" ? result : JSON.stringify(result, null, 2);
    const blob = new Blob([content], {
      type: format === "json" ? "application/json" : "text/markdown",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `run-${truncateId(id)}.${format === "json" ? "json" : "md"}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-10 w-64 rounded-lg" />
        <div className="skeleton h-40 rounded-xl" />
        <div className="skeleton h-96 rounded-xl" />
      </div>
    );
  }

  if (isError || !run) {
    return (
      <div className="rounded-xl border border-error/40 bg-error/10 p-6 text-error">
        Failed to load run details.
      </div>
    );
  }

  const metrics = [
    { label: "Composite", value: run.composite_score },
    { label: "Accuracy", value: run.accuracy_score },
    { label: "Hallucination", value: run.hallucination_score },
    { label: "Tool Precision", value: run.tool_call_precision },
    {
      label: "Latency",
      value: run.latency_ms !== null ? run.latency_ms / 10000 : null,
      display: formatLatency(run.latency_ms),
    },
  ];

  return (
    <>
      <Header
        title={`Run ${truncateId(run.id)}`}
        subtitle={run.task_description}
        action={
          <div className="flex gap-2">
            <button
              onClick={() => handleExport("json")}
              className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm transition-all duration-200 hover:bg-border/50"
            >
              <Download className="h-4 w-4" />
              JSON
            </button>
            <button
              onClick={() => handleExport("markdown")}
              className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm transition-all duration-200 hover:bg-border/50"
            >
              <Download className="h-4 w-4" />
              Markdown
            </button>
          </div>
        }
      />

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        {[
          { label: "Agent", value: run.agent_name },
          { label: "Model", value: run.llm_model },
          { label: "Status", value: <RunStatusBadge status={run.status} /> },
          { label: "Created", value: formatDate(run.created_at) },
        ].map(({ label, value }) => (
          <div key={label} className="card-hover rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-foreground/60">{label}</p>
            <div className="mt-2 text-sm font-medium">{value}</div>
          </div>
        ))}
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-5">
        {metrics.map(({ label, value, display }) => (
          <div key={label} className="card-hover rounded-xl border border-border bg-card p-4">
            <p className="text-xs text-foreground/60">{label}</p>
            <p className={`mt-2 text-lg font-semibold font-mono ${scoreColor(value)}`}>
              {display || formatScore(value)}
            </p>
            {value !== null && label !== "Latency" && (
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-border">
                <div
                  className={`h-full ${scoreBg(value)} transition-all duration-200`}
                  style={{ width: `${Math.min((value || 0) * 100, 100)}%` }}
                />
              </div>
            )}
          </div>
        ))}
        <div className="card-hover rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-foreground/60">Cost</p>
          <p className="mt-2 text-lg font-semibold font-mono">{formatCost(run.cost_usd)}</p>
        </div>
      </div>

      <h3 className="mb-4 text-lg font-medium">Agent Trace</h3>
      <TraceTimeline
        steps={run.steps || []}
        isLoading={run.status === "running" || run.status === "pending"}
        isError={false}
      />
    </>
  );
}
