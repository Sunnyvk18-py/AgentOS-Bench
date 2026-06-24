import { useState } from "react";
import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { ScoreTrendChart } from "@/components/dashboard/ScoreTrendChart";
import { ModelCompareBar } from "@/components/dashboard/ModelCompareBar";
import { NewRunModal } from "@/components/runs/NewRunModal";
import { RunStatusBadge } from "@/components/runs/RunStatusBadge";
import { useStats } from "@/hooks/useRuns";
import { formatScore, truncateId } from "@/lib/utils";
import { Plus } from "lucide-react";

export default function DashboardPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const { data, isLoading, isError } = useStats();

  return (
    <>
      <Header
        title="Dashboard"
        subtitle="Monitor agent evaluation performance and trends"
        action={
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-all duration-200 hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            New Eval Run
          </button>
        }
      />

      <div className="space-y-6">
        <StatsCards />

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <ScoreTrendChart />
          <ModelCompareBar />
        </div>

        <div className="card-hover rounded-xl border border-border bg-card p-5">
          <h3 className="mb-4 text-sm font-medium text-foreground/80">Recent Runs</h3>
          {isLoading ? (
            <div className="skeleton h-32 rounded-lg" />
          ) : isError ? (
            <p className="text-error">Failed to load recent runs.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-foreground/60">
                    <th className="pb-2 pr-4">Run ID</th>
                    <th className="pb-2 pr-4">Agent</th>
                    <th className="pb-2 pr-4">Model</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.recent_runs || []).map((run) => (
                    <tr key={run.id} className="border-b border-border/40">
                      <td className="py-2 pr-4">
                        <Link to={`/runs/${run.id}`} className="font-mono text-primary hover:underline">
                          {truncateId(run.id)}
                        </Link>
                      </td>
                      <td className="py-2 pr-4">{run.agent_name}</td>
                      <td className="py-2 pr-4">{run.llm_model}</td>
                      <td className="py-2 pr-4">
                        <RunStatusBadge status={run.status as "pending" | "running" | "completed" | "failed"} />
                      </td>
                      <td className="py-2">{formatScore(run.composite_score)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <NewRunModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}
