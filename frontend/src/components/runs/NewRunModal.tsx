import { useMemo, useState } from "react";
import { useCreateRun } from "@/hooks/useRuns";
import { useAgentsLive } from "@/hooks/useAgentStream";
import { AgentUploadModal } from "@/components/agents/AgentUploadModal";
import type { AgentInfo } from "@/lib/types";
import { X } from "lucide-react";

const MODELS = ["mock-model", "gpt-4o", "claude-3-5-sonnet", "llama-3.1-8b", "deepseek-chat"];

interface NewRunModalProps {
  open: boolean;
  onClose: () => void;
}

function ConfigField({
  name,
  schema,
  value,
  onChange,
}: {
  name: string;
  schema: { type?: string; default?: unknown; description?: string };
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  const fieldType = schema.type || "string";

  if (fieldType === "float" || fieldType === "int") {
    return (
      <div>
        <label className="mb-1 block text-sm text-foreground/70">{name}</label>
        <input
          type="number"
          step={fieldType === "float" ? 0.01 : 1}
          value={value as number}
          onChange={(e) =>
            onChange(fieldType === "float" ? parseFloat(e.target.value) : parseInt(e.target.value, 10))
          }
          className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
        />
      </div>
    );
  }

  if (fieldType === "bool" || fieldType === "boolean") {
    return (
      <label className="flex items-center gap-2 text-sm text-foreground/70">
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(e.target.checked)}
        />
        {name}
      </label>
    );
  }

  return (
    <div>
      <label className="mb-1 block text-sm text-foreground/70">{name}</label>
      <input
        type="text"
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
      />
    </div>
  );
}

export function NewRunModal({ open, onClose }: NewRunModalProps) {
  const [agentName, setAgentName] = useState("mock");
  const [llmModel, setLlmModel] = useState("mock-model");
  const [task, setTask] = useState("");
  const [agentConfig, setAgentConfig] = useState<Record<string, unknown>>({});
  const [uploadOpen, setUploadOpen] = useState(false);
  const createRun = useCreateRun();
  const { data: agents } = useAgentsLive();

  const selectedAgent: AgentInfo | undefined = useMemo(
    () => (agents || []).find((a) => a.name === agentName),
    [agents, agentName]
  );

  const schemaEntries = useMemo(
    () => Object.entries(selectedAgent?.config_schema || {}),
    [selectedAgent]
  );

  if (!open) return null;

  const handleAgentChange = (name: string) => {
    setAgentName(name);
    const agent = (agents || []).find((a) => a.name === name);
    const defaults: Record<string, unknown> = {};
    Object.entries(agent?.config_schema || {}).forEach(([key, schema]) => {
      defaults[key] = schema.default ?? "";
    });
    setAgentConfig(defaults);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createRun.mutateAsync({
      agent_name: agentName,
      llm_model: llmModel,
      task_description: task,
      agent_config: Object.keys(agentConfig).length ? agentConfig : undefined,
    });
    setTask("");
    onClose();
  };

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
        <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-border bg-card p-6 shadow-glow">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">New Eval Run</h2>
            <button onClick={onClose} className="text-foreground/60 hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm text-foreground/70">Agent</label>
              <select
                value={agentName}
                onChange={(e) => handleAgentChange(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
              >
                {(agents || [{ name: "mock" }]).map((a) => (
                  <option key={a.name} value={a.name}>
                    {a.name}
                  </option>
                ))}
              </select>
              {selectedAgent?.description && (
                <p className="mt-1 text-xs text-foreground/50">{selectedAgent.description}</p>
              )}
              <button
                type="button"
                onClick={() => setUploadOpen(true)}
                className="mt-2 text-sm text-primary hover:underline"
              >
                Upload Agent
              </button>
            </div>

            {schemaEntries.map(([key, schema]) => (
              <ConfigField
                key={key}
                name={key}
                schema={schema}
                value={agentConfig[key] ?? schema.default ?? ""}
                onChange={(val) => setAgentConfig((prev) => ({ ...prev, [key]: val }))}
              />
            ))}

            <div>
              <label className="mb-1 block text-sm text-foreground/70">Model</label>
              <select
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
              >
                {MODELS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm text-foreground/70">Task Description</label>
              <textarea
                value={task}
                onChange={(e) => setTask(e.target.value)}
                required
                rows={4}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                placeholder="Describe the agent task to evaluate..."
              />
            </div>
            {createRun.isError && (
              <p className="text-sm text-error">Failed to create run. Please try again.</p>
            )}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-border px-4 py-2 text-sm transition-all duration-200 hover:bg-border/50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createRun.isPending}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:bg-primary/90 disabled:opacity-50"
              >
                {createRun.isPending ? "Starting..." : "Start Eval Run"}
              </button>
            </div>
          </form>
        </div>
      </div>

      <AgentUploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </>
  );
}
