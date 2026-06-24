import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { BenchmarkTable } from "@/components/benchmark/BenchmarkTable";
import { RadarChart } from "@/components/benchmark/RadarChart";
import { useBenchmarks, useCreateBenchmark } from "@/hooks/useBenchmark";
import { useAgents } from "@/hooks/useReports";
import { formatDate } from "@/lib/utils";

const AVAILABLE_MODELS = ["gpt-4o", "claude-3-5-sonnet", "llama-3.1-8b", "deepseek-chat", "mock-model"];

export default function BenchmarkPage() {
  const { data: benchmarks, isLoading, isError } = useBenchmarks();
  const { data: agents } = useAgents();
  const createBenchmark = useCreateBenchmark();

  const [name, setName] = useState("");
  const [task, setTask] = useState("");
  const [agentName, setAgentName] = useState("mock");
  const [selectedModels, setSelectedModels] = useState<string[]>(["gpt-4o", "mock-model"]);
  const [activeId, setActiveId] = useState<string>("");

  const activeBenchmark = benchmarks?.find((b) => b.id === activeId) || benchmarks?.[0];

  const toggleModel = (model: string) => {
    setSelectedModels((prev) =>
      prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createBenchmark.mutateAsync({
      benchmark_name: name,
      task_description: task,
      models: selectedModels,
      agent_name: agentName,
    });
    setName("");
    setTask("");
  };

  return (
    <>
      <Header title="Benchmark" subtitle="Compare LLM models on identical agent tasks" />

      <div className="mb-8 card-hover rounded-xl border border-border bg-card p-5">
        <h3 className="mb-4 text-sm font-medium">New Benchmark</h3>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="Benchmark name"
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
          />
          <select
            value={agentName}
            onChange={(e) => setAgentName(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
          >
            {(agents || [{ name: "mock" }]).map((a) => (
              <option key={a.name} value={a.name}>
                {a.name}
              </option>
            ))}
          </select>
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            required
            placeholder="Task description"
            rows={3}
            className="lg:col-span-2 rounded-lg border border-border bg-background px-3 py-2 text-sm"
          />
          <div className="lg:col-span-2 flex flex-wrap gap-3">
            {AVAILABLE_MODELS.map((model) => (
              <label key={model} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedModels.includes(model)}
                  onChange={() => toggleModel(model)}
                />
                {model}
              </label>
            ))}
          </div>
          <button
            type="submit"
            disabled={createBenchmark.isPending || selectedModels.length < 2}
            className="w-fit rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:bg-primary/90 disabled:opacity-50"
          >
            {createBenchmark.isPending ? "Running..." : "Start Benchmark"}
          </button>
        </form>
      </div>

      {isLoading ? (
        <div className="skeleton h-64 rounded-xl" />
      ) : isError ? (
        <div className="rounded-xl border border-error/40 bg-error/10 p-4 text-error">
          Failed to load benchmarks.
        </div>
      ) : activeBenchmark ? (
        <div className="space-y-6">
          <BenchmarkTable benchmark={activeBenchmark} />
          <RadarChart benchmark={activeBenchmark} />
        </div>
      ) : (
        <p className="text-foreground/60">No benchmarks yet. Create one above.</p>
      )}

      {benchmarks && benchmarks.length > 0 && (
        <div className="mt-8 card-hover rounded-xl border border-border bg-card p-5">
          <h3 className="mb-4 text-sm font-medium">Benchmark History</h3>
          <div className="space-y-2">
            {benchmarks.map((b) => (
              <button
                key={b.id}
                onClick={() => setActiveId(b.id)}
                className={`flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left text-sm transition-all duration-200 ${
                  activeBenchmark?.id === b.id ? "border-primary bg-primary/10" : "border-border hover:bg-border/30"
                }`}
              >
                <span>{b.benchmark_name}</span>
                <span className="flex items-center gap-2 text-foreground/60">
                  <span className="rounded-full bg-success/15 px-2 py-0.5 text-xs text-success">
                    🏆 {b.winner_model}
                  </span>
                  {formatDate(b.created_at)}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
