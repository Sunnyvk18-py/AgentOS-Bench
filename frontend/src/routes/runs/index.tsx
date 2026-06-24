import { useState } from "react";
import { Header } from "@/components/layout/Header";
import { RunsTable } from "@/components/runs/RunsTable";
import { NewRunModal } from "@/components/runs/NewRunModal";
import { Plus } from "lucide-react";

export default function RunsPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");

  return (
    <>
      <Header
        title="Eval Runs"
        subtitle="Browse, filter, and manage all evaluation runs"
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

      <div className="mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <RunsTable statusFilter={statusFilter} />
      <NewRunModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}
