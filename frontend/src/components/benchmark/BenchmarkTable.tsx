import { useMemo } from "react";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import type { BenchmarkResult } from "@/lib/types";
import { formatCost, formatLatency, formatScore } from "@/lib/utils";

interface BenchmarkTableProps {
  benchmark: BenchmarkResult;
}

type Row = {
  model: string;
  accuracy: number | null;
  hallucination: number | null;
  latency_ms: number | null;
  cost_usd: number | null;
  composite_score: number | null;
  isWinner: boolean;
};

export function BenchmarkTable({ benchmark }: BenchmarkTableProps) {
  const data = useMemo<Row[]>(
    () =>
      benchmark.models_compared.map((model) => {
        const result = benchmark.results[model] || {
          accuracy: null,
          hallucination: null,
          latency_ms: null,
          cost_usd: null,
          composite_score: null,
        };
        return {
          model,
          accuracy: result.accuracy,
          hallucination: result.hallucination,
          latency_ms: result.latency_ms,
          cost_usd: result.cost_usd,
          composite_score: result.composite_score,
          isWinner: model === benchmark.winner_model,
        };
      }),
    [benchmark]
  );

  const columns = useMemo<ColumnDef<Row>[]>(
    () => [
      {
        accessorKey: "model",
        header: "Model",
        cell: ({ row, getValue }) => (
          <span className={row.original.isWinner ? "font-semibold text-success" : ""}>
            {getValue<string>()}
            {row.original.isWinner && " 🏆"}
          </span>
        ),
      },
      {
        accessorKey: "accuracy",
        header: "Accuracy",
        cell: ({ getValue }) => formatScore(getValue<number | null>()),
      },
      {
        accessorKey: "hallucination",
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
        accessorKey: "composite_score",
        header: "Composite",
        cell: ({ getValue }) => formatScore(getValue<number | null>()),
      },
    ],
    []
  );

  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-card">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => (
                <th key={header.id} className="px-4 py-3 text-left font-medium text-foreground/70">
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
              className={`border-b border-border/50 ${row.original.isWinner ? "bg-success/5" : ""}`}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
