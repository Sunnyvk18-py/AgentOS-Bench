from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScoreWeights(BaseModel):
    accuracy_weight: float = 0.2
    hallucination_weight: float = 0.2
    tool_precision_weight: float = 0.2
    latency_weight: float = 0.2
    cost_weight: float = 0.2


class EvalRunCreate(BaseModel):
    agent_name: str
    llm_model: str
    task_description: str
    agent_config: dict[str, Any] | None = None


class AgentStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    step_index: int
    step_type: str
    content: str
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: dict[str, Any] | None = None
    duration_ms: int
    timestamp: datetime


class EvalRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_name: str
    llm_model: str
    task_description: str
    status: str
    composite_score: float | None = None
    accuracy_score: float | None = None
    hallucination_score: float | None = None
    tool_call_precision: float | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None
    total_steps: int | None = None
    created_at: datetime
    completed_at: datetime | None = None
    steps: list[AgentStepResponse] = Field(default_factory=list)


class BenchmarkRequest(BaseModel):
    benchmark_name: str
    task_description: str
    models: list[str]
    agent_name: str
    agent_config: dict[str, Any] | None = None


class BenchmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    benchmark_name: str
    task_description: str
    models_compared: list[str]
    results: dict[str, dict[str, Any]]
    winner_model: str
    created_at: datetime


class ReportRequest(BaseModel):
    run_id: str
    format: str = "json"


class ScoreBreakdown(BaseModel):
    composite_score: float | None = None
    accuracy_score: float | None = None
    hallucination_score: float | None = None
    tool_call_precision: float | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None
    weights: ScoreWeights = Field(default_factory=ScoreWeights)
