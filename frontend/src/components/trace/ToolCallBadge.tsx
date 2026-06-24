import { Wrench } from "lucide-react";

interface ToolCallBadgeProps {
  toolName: string;
}

export function ToolCallBadge({ toolName }: ToolCallBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-xs text-primary">
      <Wrench className="h-3 w-3" />
      {toolName}
    </span>
  );
}
