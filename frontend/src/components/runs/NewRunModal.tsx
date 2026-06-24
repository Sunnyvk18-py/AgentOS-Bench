import { useState } from "react";
import { useCreateRun } from "@/hooks/useRuns";
import { useAgents } from "@/hooks/useReports";
import { X } from "lucide-react";

const MODELS = ["mock-model", "gpt-4o", "claude-3-5-sonnet", "llama-3.1-8b", "deepseek-chat"];

interface NewRunModalProps {
  open: boolean;
  onClose: () => void;
}

export function NewRunModal({ open, onClose }: NewRunModalProps) {
  const [agentName, setAgentName] = useState("mock");
  const [llmModel, setLlmModel] = useState("mock-model");
  const [task, setTask] = useState("");
  const createRun = useCreateRun();
  const { data: agents } = useAgents();

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createRun.mutateAsync({
      agent_name: agentName,
      llm_model: llmModel,
      task_description: task,
    });
    setTask("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-glow">
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
              onChange={(e) => setAgentName(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            >
              {(agents || [{ name: "mock" }]).map((a) => (
                <option key={a.name} value={a.name}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
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
  );
}
