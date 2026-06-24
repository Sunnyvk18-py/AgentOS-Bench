import type { AgentStep } from "@/lib/types";
import { Brain, CheckCircle, Database, Wrench } from "lucide-react";
import { StepCard } from "./StepCard";

const icons = {
  reasoning: Brain,
  tool_call: Wrench,
  memory_read: Database,
  output: CheckCircle,
};

interface TraceTimelineProps {
  steps: AgentStep[];
  isLoading?: boolean;
  isError?: boolean;
}

export function TraceTimeline({ steps, isLoading, isError }: TraceTimelineProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="skeleton h-20 rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-error/40 bg-error/10 p-4 text-error">
        Failed to load trace timeline.
      </div>
    );
  }

  if (!steps.length) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 text-center text-foreground/60">
        No steps recorded yet. Trace will update live while the run is in progress.
      </div>
    );
  }

  return (
    <div className="relative space-y-4 pl-8">
      <div className="absolute bottom-0 left-3 top-0 w-px bg-border" />
      {steps.map((step, index) => {
        const Icon = icons[step.step_type] || Brain;
        return (
          <div
            key={step.id}
            className="relative animate-[fadeIn_0.4s_ease-in_forwards] opacity-0"
            style={{ animationDelay: `${index * 100}ms`, animationFillMode: "forwards" }}
          >
            <div className="absolute -left-8 top-4 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-card">
              <Icon className="h-3.5 w-3.5 text-primary" />
            </div>
            <StepCard step={step} index={index} />
          </div>
        );
      })}
    </div>
  );
}
