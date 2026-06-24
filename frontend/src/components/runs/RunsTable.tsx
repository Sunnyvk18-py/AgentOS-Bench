import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { useDeleteRun, useRuns } from "@/hooks/useRuns";
import type { EvalRun } from "@/lib/types";
import {
  exportCsv,
  formatCost,
  formatDate,
  formatLatency,
  formatScore,
  scoreColor,
  truncateId,
} from "@/lib/utils";
import { RunStatusBadge } from "./RunStatusBadge";
import { Download, Trash2 } from "lucide-react";

interface RunsTableProps {
  statusFilter?: string;
}

export function RunsTable({ statusFilter = "" }: RunsTableProps) {
  const navigate = useNavigate();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [rowSelection, setRowSelection] = useState({});
  const { data, isLoading, isError } = useRuns({
    page_size: 100,
    status: statusFilter || undefined,
  });
  const deleteRun = useDeleteRun();

  const columns = useMemo<ColumnDef<EvalRun>[]>(
    () => [
      {
        id: "select",
        header: ({ table }) => (
          <input
            type="checkbox"
            checked={table.getIsAllPageRowsSelected()}
            onChange={table.getToggleAllPageRowsSelectedHandler()}
          />
        ),
        cell: ({ row }) => (
          <input
            type="checkbox"
            checked={row.getIsSelected()}
            onChange={row.getToggleSelectedHandler()}
            onClick={(e) => e.stopPropagation()}
          />
        ),
      },
      {
        accessorKey: "id",
        header: "Run ID",
        cell: ({ getValue }) => (
          <span className="font-mono text-xs">{truncateId(getValue<string>())}</span>
        ),
      },
      { accessorKey: "agent_name", header: "Agent" },
      { accessorKey: "llm_model", header: "Model" },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ getValue }) => <RunStatusBadge status={getValue<EvalRun["status"]>()} />,
      },
      {
        accessorKey: "composite_score",
        header: "Composite",
        cell: ({ getValue }) => (
          <span className={scoreColor(getValue<number | null>())}>
            {formatScore(getValue<number | null>())}
          </span>
        ),
      },
      {
        accessorKey: "accuracy_score",
        header: "Accuracy",
        cell: ({ getValue }) => formatScore(getValue<number | null>()),
      },
      {
        accessorKey: "hallucination_score",
        header: "Hallucination",
        cell: ({ getValue }) => formatScore(getValue<number | null>()),
      },
      {
        accessorKey: "latency_ms",
        header: "Latency",
        cell: ({ getValue }) => formatLatency(getValue<number | null>()),
      },
      {
        accessorKey: "cost_usd",
        header: "Cost",
        cell: ({ getValue }) => formatCost(getValue<number | null>()),
      },
      {
        accessorKey: "created_at",
        header: "Created",
        cell: ({ getValue }) => formatDate(getValue<string>()),
      },
      {
        id: "actions",
        header: "Actions",
        cell: ({ row }) => (
          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteRun.mutate(row.original.id);
            }}
            className="text-error hover:text-error/80"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        ),
      },
    ],
    [deleteRun]
  );

  const table = useReactTable({
    data: data?.items || [],
    columns,
    state: { sorting, globalFilter, rowSelection },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  });

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="skeleton h-10 rounded-lg" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-error/40 bg-error/10 p-4 text-error">
        Failed to load eval runs.
      </div>
    );
  }

  const handleBulkDelete = () => {
    const selected = table.getFilteredSelectedRowModel().rows;
    selected.forEach((row) => deleteRun.mutate(row.original.id));
    setRowSelection({});
  };

  const handleExportCsv = () => {
    const rows = table.getFilteredRowModel().rows.map(({ original: r }) => ({
      id: r.id,
      agent: r.agent_name,
      model: r.llm_model,
      status: r.status,
      composite: r.composite_score,
      accuracy: r.accuracy_score,
      latency_ms: r.latency_ms,
      cost_usd: r.cost_usd,
      created_at: r.created_at,
    }));
    exportCsv(rows, "eval-runs.csv");
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <input
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder="Filter runs..."
          className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
        />
        <button
          onClick={handleBulkDelete}
          className="rounded-lg border border-border px-3 py-2 text-sm transition-all duration-200 hover:bg-border/50"
        >
          Delete Selected
        </button>
        <button
          onClick={handleExportCsv}
          className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm transition-all duration-200 hover:bg-border/50"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead className="border-b border-border bg-card">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="cursor-pointer px-3 py-3 text-left font-medium text-foreground/70"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => navigate(`/runs/${row.original.id}`)}
                className="cursor-pointer border-b border-border/50 transition-all duration-200 hover:bg-border/20"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-foreground/60">
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          {[10, 25, 50].map((size) => (
            <button
              key={size}
              onClick={() => table.setPageSize(size)}
              className={`rounded px-2 py-1 ${table.getState().pagination.pageSize === size ? "bg-primary/20 text-primary" : "hover:bg-border/50"}`}
            >
              {size}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="rounded border border-border px-2 py-1 disabled:opacity-40"
          >
            Prev
          </button>
          <span>
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="rounded border border-border px-2 py-1 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
