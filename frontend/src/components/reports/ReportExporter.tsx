import { Download } from "lucide-react";

interface ReportExporterProps {
  runId: string;
  onExport: (format: "json" | "markdown") => void;
  isLoading?: boolean;
}

export function ReportExporter({ runId, onExport, isLoading }: ReportExporterProps) {
  if (!runId) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 text-foreground/60">
        Select a run to export its report.
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-3">
      <button
        onClick={() => onExport("json")}
        disabled={isLoading}
        className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:bg-primary/90 disabled:opacity-50"
      >
        <Download className="h-4 w-4" />
        Download JSON
      </button>
      <button
        onClick={() => onExport("markdown")}
        disabled={isLoading}
        className="flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm transition-all duration-200 hover:bg-border/50 disabled:opacity-50"
      >
        <Download className="h-4 w-4" />
        Download Markdown
      </button>
    </div>
  );
}
