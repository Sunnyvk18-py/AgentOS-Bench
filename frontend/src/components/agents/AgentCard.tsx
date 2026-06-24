import { cn } from "@/lib/utils";

interface AgentCardProps {
  name: string;
  description: string;
  configSchema: Record<string, unknown>;
  isBuiltIn?: boolean;
  isNew?: boolean;
}

export function AgentCard({
  name,
  description,
  configSchema,
  isBuiltIn = false,
  isNew = false,
}: AgentCardProps) {
  const schemaKeys = Object.keys(configSchema || {});

  return (
    <div
      className={cn(
        "card-hover relative rounded-xl border border-border bg-card p-4 transition-all duration-300",
        isNew && "ring-1 ring-success/50"
      )}
    >
      {isNew && (
        <span className="absolute right-3 top-3 animate-pulse rounded-full bg-success/20 px-2 py-0.5 text-xs text-success">
          New
        </span>
      )}
      <div className="mb-2 flex items-center gap-2">
        <h4 className="font-semibold capitalize">{name}</h4>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-xs",
            isBuiltIn ? "bg-border text-foreground/70" : "bg-primary/15 text-primary"
          )}
        >
          {isBuiltIn ? "Built-in" : "Custom"}
        </span>
      </div>
      <p className="mb-3 text-sm text-foreground/60">{description || "No description provided."}</p>
      <div className="flex flex-wrap gap-1.5">
        {schemaKeys.length ? (
          schemaKeys.map((key) => (
            <span
              key={key}
              className="rounded-full bg-background px-2 py-0.5 font-mono text-xs text-foreground/50"
            >
              {key}
            </span>
          ))
        ) : (
          <span className="text-xs text-foreground/40">No config options</span>
        )}
      </div>
    </div>
  );
}
