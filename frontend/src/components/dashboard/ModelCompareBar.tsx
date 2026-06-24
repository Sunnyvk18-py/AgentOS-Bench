import { useStats } from "@/hooks/useRuns";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function ModelCompareBar() {
  const { data, isLoading, isError } = useStats();

  if (isLoading) return <div className="skeleton h-72 rounded-xl" />;
  if (isError || !data) {
    return (
      <div className="rounded-xl border border-error/40 bg-error/10 p-4 text-error">
        Failed to load model comparison.
      </div>
    );
  }

  const chartData = Object.entries(data.model_comparison).map(([model, score]) => ({
    model,
    score: score * 100,
  }));

  return (
    <div className="card-hover rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-medium text-foreground/80">Model Comparison</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} layout="vertical">
          <CartesianGrid stroke="#2D3148" strokeDasharray="3 3" />
          <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" fontSize={12} />
          <YAxis type="category" dataKey="model" stroke="#94a3b8" fontSize={11} width={120} />
          <Tooltip
            contentStyle={{ background: "#1A1D27", border: "1px solid #2D3148" }}
            formatter={(value: number) => [`${value.toFixed(1)}%`, "Avg Score"]}
          />
          <Bar dataKey="score" fill="#6366F1" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
