import type {
  AgentInfo,
  APIResponse,
  BenchmarkRequest,
  BenchmarkResult,
  DashboardStats,
  EvalRun,
  EvalRunCreate,
  RunsListResponse,
  ScoreBreakdown,
} from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("text/markdown")) {
    return (await response.text()) as T;
  }

  const json = (await response.json()) as APIResponse<T> | T;
  if (typeof json === "object" && json !== null && "success" in json) {
    const wrapped = json as APIResponse<T>;
    if (!wrapped.success) {
      throw new Error(wrapped.error || "Unknown API error");
    }
    return wrapped.data as T;
  }
  return json as T;
}

export const api = {
  getStats: () => request<DashboardStats>("/api/stats"),
  getRuns: (params?: { page?: number; page_size?: number; status?: string; model?: string }) => {
    const search = new URLSearchParams();
    if (params?.page) search.set("page", String(params.page));
    if (params?.page_size) search.set("page_size", String(params.page_size));
    if (params?.status) search.set("status", params.status);
    if (params?.model) search.set("model", params.model);
    const qs = search.toString();
    return request<RunsListResponse>(`/api/runs${qs ? `?${qs}` : ""}`);
  },
  getRun: (id: string) => request<EvalRun>(`/api/runs/${id}`),
  createRun: (payload: EvalRunCreate) =>
    request<EvalRun>("/api/runs", { method: "POST", body: JSON.stringify(payload) }),
  deleteRun: (id: string) =>
    request<{ deleted: string }>(`/api/runs/${id}`, { method: "DELETE" }),
  getRunScore: (id: string) => request<ScoreBreakdown>(`/api/runs/${id}/score`),
  getBenchmarks: () => request<BenchmarkResult[]>("/api/benchmarks"),
  getBenchmark: (id: string) => request<BenchmarkResult>(`/api/benchmarks/${id}`),
  createBenchmark: (payload: BenchmarkRequest) =>
    request<{ benchmark_name: string; status: string; models: string[] }>("/api/benchmarks", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getAgents: () => request<AgentInfo[]>("/api/agents"),
  exportReport: (runId: string, format: "json" | "markdown") =>
    request<Record<string, unknown> | string>("/api/reports/export", {
      method: "POST",
      body: JSON.stringify({ run_id: runId, format }),
    }),
};
