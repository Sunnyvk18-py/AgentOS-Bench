import { useStats } from "@/hooks/useRuns";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function ScoreTrendChart() {
  const { data, isLoading, isError } = useStats();

  if (isLoading) return <div className="skeleton h-72 rounded-xl" />;
  if (isError || !data) {
    return (
      <div className="rounded-xl border border-error/40 bg-error/10 p-4 text-error">
        Failed to load score trend.
      </div>
    );
  }

  const chartData = data.score_trend.slice(-30).map((item, index) => ({
    run: index + 1,
    score: item.composite_score ? item.composite_score * 100 : 0,
  }));

  return (
    <div className="card-hover rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-medium text-foreground/80">Score Trend (Last 30 Runs)</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={chartData}>
          <CartesianGrid stroke="#2D3148" strokeDasharray="3 3" />
          <XAxis dataKey="run" stroke="#94a3b8" fontSize={12} />
          <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={12} />
          <Tooltip
            contentStyle={{ background: "#1A1D27", border: "1px solid #2D3148" }}
            formatter={(value: number) => [`${value.toFixed(1)}%`, "Score"]}
          />
          <Line type="monotone" dataKey="score" stroke="#6366F1" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
