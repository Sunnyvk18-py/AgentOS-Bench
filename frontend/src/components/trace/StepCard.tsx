import { useState } from "react";
import type { AgentStep } from "@/lib/types";
import { formatLatency } from "@/lib/utils";
import { ToolCallBadge } from "./ToolCallBadge";
import { ChevronDown } from "lucide-react";

interface StepCardProps {
  step: AgentStep;
  index: number;
}

export function StepCard({ step, index }: StepCardProps) {
  const [open, setOpen] = useState(index === 0);

  return (
    <div
      className="rounded-xl border border-border bg-card p-4 transition-all duration-200 ease-in-out"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-primary">#{step.step_index + 1}</span>
          <span className="text-sm font-medium capitalize">{step.step_type.replace("_", " ")}</span>
          {step.tool_name && <ToolCallBadge toolName={step.tool_name} />}
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-border px-2 py-0.5 text-xs font-mono">
            {formatLatency(step.duration_ms)}
          </span>
          <ChevronDown
            className={`h-4 w-4 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {open && (
        <div className="mt-3 space-y-2 border-t border-border pt-3 text-sm text-foreground/80">
          <p className="whitespace-pre-wrap">{step.content}</p>
          {step.tool_input && (
            <pre className="overflow-x-auto rounded-lg bg-background p-2 font-mono text-xs">
              {JSON.stringify(step.tool_input, null, 2)}
            </pre>
          )}
          {step.tool_output && (
            <pre className="overflow-x-auto rounded-lg bg-background p-2 font-mono text-xs">
              {JSON.stringify(step.tool_output, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
