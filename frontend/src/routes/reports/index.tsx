import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { ReportExporter } from "@/components/reports/ReportExporter";
import { useExportReport, useRunsList } from "@/hooks/useReports";
import { truncateId } from "@/lib/utils";

export default function ReportsPage() {
  const { data, isLoading, isError } = useRunsList();
  const [selectedRunId, setSelectedRunId] = useState("");
  const [preview, setPreview] = useState("");
  const exportReport = useExportReport();

  const handleExport = async (format: "json" | "markdown") => {
    if (!selectedRunId) return;
    const result = await exportReport.mutateAsync({ runId: selectedRunId, format });
    const content = typeof result === "string" ? result : JSON.stringify(result, null, 2);
    setPreview(content);

    const blob = new Blob([content], {
      type: format === "json" ? "application/json" : "text/markdown",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report-${truncateId(selectedRunId)}.${format === "json" ? "json" : "md"}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <Header title="Reports" subtitle="Preview and export evaluation reports" />

      {isLoading ? (
        <div className="skeleton h-10 w-full max-w-md rounded-lg" />
      ) : isError ? (
        <div className="rounded-xl border border-error/40 bg-error/10 p-4 text-error">
          Failed to load runs.
        </div>
      ) : (
        <select
          value={selectedRunId}
          onChange={(e) => {
            setSelectedRunId(e.target.value);
            setPreview("");
          }}
          className="mb-6 w-full max-w-md rounded-lg border border-border bg-background px-3 py-2 text-sm"
        >
          <option value="">Select a run...</option>
          {(data?.items || []).map((run) => (
            <option key={run.id} value={run.id}>
              {truncateId(run.id)} — {run.agent_name} ({run.status})
            </option>
          ))}
        </select>
      )}

      <ReportExporter
        runId={selectedRunId}
        onExport={handleExport}
        isLoading={exportReport.isPending}
      />

      {preview && (
        <div className="mt-6 card-hover rounded-xl border border-border bg-card p-5">
          <h3 className="mb-3 text-sm font-medium text-foreground/80">Report Preview</h3>
          <pre className="max-h-96 overflow-auto rounded-lg bg-background p-4 font-mono text-xs text-foreground/80">
            {preview}
          </pre>
        </div>
      )}
    </>
  );
}
