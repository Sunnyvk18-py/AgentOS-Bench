export interface AgentStep {
  id: string;
  run_id: string;
  step_index: number;
  step_type: "reasoning" | "tool_call" | "memory_read" | "output";
  content: string;
  tool_name: string | null;
  tool_input: Record<string, unknown> | null;
  tool_output: Record<string, unknown> | null;
  duration_ms: number;
  timestamp: string;
}

export interface EvalRun {
  id: string;
  agent_name: string;
  llm_model: string;
  task_description: string;
  status: "pending" | "running" | "completed" | "failed";
  composite_score: number | null;
  accuracy_score: number | null;
  hallucination_score: number | null;
  tool_call_precision: number | null;
  latency_ms: number | null;
  cost_usd: number | null;
  total_steps: number | null;
  created_at: string;
  completed_at: string | null;
  steps?: AgentStep[];
}

export interface RunsListResponse {
  items: EvalRun[];
  total: number;
  page: number;
  page_size: number;
}

export interface BenchmarkResult {
  id: string;
  benchmark_name: string;
  task_description: string;
  models_compared: string[];
  results: Record<
    string,
    {
      accuracy: number | null;
      hallucination: number | null;
      latency_ms: number | null;
      cost_usd: number | null;
      composite_score: number | null;
      run_id?: string;
    }
  >;
  winner_model: string;
  created_at: string;
}

export interface AgentInfo {
  name: string;
  description: string;
  config_schema: Record<string, unknown>;
}

export interface DashboardStats {
  total_runs: number;
  avg_composite_score: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  score_trend: Array<{
    run_id: string;
    composite_score: number | null;
    created_at: string;
  }>;
  model_comparison: Record<string, number>;
  recent_runs: Array<{
    id: string;
    agent_name: string;
    llm_model: string;
    status: string;
    composite_score: number | null;
    created_at: string;
  }>;
}

export interface ScoreBreakdown {
  composite_score: number | null;
  accuracy_score: number | null;
  hallucination_score: number | null;
  tool_call_precision: number | null;
  latency_ms: number | null;
  cost_usd: number | null;
}

export interface APIResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

export interface EvalRunCreate {
  agent_name: string;
  llm_model: string;
  task_description: string;
  agent_config?: Record<string, unknown>;
}

export interface BenchmarkRequest {
  benchmark_name: string;
  task_description: string;
  models: string[];
  agent_name: string;
  agent_config?: Record<string, unknown>;
}
