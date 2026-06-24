import { useEffect, useState } from "react";
import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { BenchmarkResult } from "@/lib/types";

interface RadarChartProps {
  benchmark: BenchmarkResult;
}

export function RadarChart({ benchmark }: RadarChartProps) {
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setAnimate(true), 100);
    return () => clearTimeout(timer);
  }, [benchmark.id]);

  const metrics = ["accuracy", "hallucination", "latency", "cost", "composite"] as const;
  const chartData = metrics.map((metric) => {
    const row: Record<string, string | number> = { metric };
    benchmark.models_compared.forEach((model) => {
      const result = benchmark.results[model];
      if (!result) return;
      if (metric === "latency") {
        const ms = result.latency_ms || 0;
        row[model] = ms <= 500 ? 100 : Math.max(0, 100 - ((ms - 500) / 9500) * 100);
      } else if (metric === "cost") {
        const cost = result.cost_usd || 0;
        row[model] = cost <= 0.001 ? 100 : Math.max(0, 100 - ((cost - 0.001) / 0.099) * 100);
      } else if (metric === "hallucination") {
        row[model] = (1 - (result.hallucination || 0)) * 100;
      } else if (metric === "composite") {
        row[model] = (result.composite_score || 0) * 100;
      } else {
        row[model] = (result.accuracy || 0) * 100;
      }
    });
    return row;
  });

  const colors = ["#6366F1", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"];

  return (
    <div className="card-hover rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-medium text-foreground/80">Multi-Metric Radar</h3>
      <ResponsiveContainer width="100%" height={320}>
        <RechartsRadar data={chartData}>
          <PolarGrid stroke="#2D3148" />
          <PolarAngleAxis dataKey="metric" stroke="#94a3b8" fontSize={12} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#94a3b8" />
          <Tooltip contentStyle={{ background: "#1A1D27", border: "1px solid #2D3148" }} />
          <Legend />
          {benchmark.models_compared.map((model, i) => (
            <Radar
              key={model}
              name={model}
              dataKey={model}
              stroke={colors[i % colors.length]}
              fill={colors[i % colors.length]}
              fillOpacity={0.2}
              isAnimationActive={animate}
              animationDuration={800}
            />
          ))}
        </RechartsRadar>
      </ResponsiveContainer>
    </div>
  );
}
