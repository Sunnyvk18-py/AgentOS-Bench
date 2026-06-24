import type { EvalRun } from "@/lib/types";
import { cn } from "@/lib/utils";

const statusStyles: Record<string, string> = {
  pending: "bg-warning/15 text-warning border-warning/30",
  running: "bg-primary/15 text-primary border-primary/30",
  completed: "bg-success/15 text-success border-success/30",
  failed: "bg-error/15 text-error border-error/30",
};

interface RunStatusBadgeProps {
  status: EvalRun["status"];
}

export function RunStatusBadge({ status }: RunStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full border px-2 py-0.5 text-xs font-medium capitalize",
        statusStyles[status] || statusStyles.pending
      )}
    >
      {status}
    </span>
  );
}
