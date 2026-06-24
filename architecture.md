# AgentOS Bench — Architecture

## 1. System Overview

```
┌─────────────┐     REST/JSON      ┌──────────────────┐
│   React     │ ◄──────────────►  │  FastAPI Backend  │
│  Dashboard  │                    │  (Eval Engine)    │
└─────────────┘                    └────────┬─────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
              ┌─────▼─────┐          ┌──────▼──────┐         ┌──────▼──────┐
              │  SQLite   │          │   Kafka     │         │ Agent       │
              │  (async)  │          │  (events)   │         │ Plugins     │
              └───────────┘          └─────────────┘         └─────────────┘
```

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| Frontend | React 18, TanStack Query/Table, Recharts | Dashboard, trace viewer, benchmarks |
| API | FastAPI, Pydantic v2 | REST endpoints, background tasks |
| Core | EvalRunner, BenchmarkHarness, Scoring | Orchestration and metrics |
| Agents | BaseAgent plugins (Mock, LangGraph) | Execute tasks, emit steps |
| Events | Kafka producer/consumer | Stream step events, graceful degradation |
| Storage | SQLAlchemy async + SQLite | Runs, steps, benchmark results |

## 2. Data Flow

1. **User triggers run** — Frontend POST `/api/runs` with agent, model, task.
2. **API** — Creates `EvalRun` (status=pending), schedules background task.
3. **EvalRunner** — Sets status=running, registers `AgentTracer`, calls `agent.execute(task)`.
4. **Agent** — Executes reasoning/tool steps; tracer records each step.
5. **Kafka Producer** — Emits `agent_step` events (non-blocking if Kafka down).
6. **Scoring** — Computes accuracy, hallucination, tool precision, latency, cost → composite score.
7. **DB Update** — Persists steps and scores; status=completed.
8. **Kafka Consumer** — Background task persists streamed steps (idempotent by step_index).
9. **Frontend polling** — TanStack Query refetches every 2s for running/pending runs.

## 3. Scoring Pipeline

```
Agent Output + Trace
        │
        ├── compute_accuracy_score(expected, actual)
        │     └── token overlap (40%) + sentence-transformers cosine (60%)
        │
        ├── compute_hallucination_score(output, context)
        │     └── LLM-as-judge (Claude) or keyword heuristic fallback
        │
        ├── compute_tool_precision(expected_tools, actual_tools)
        │     └── F1 on tool name sets
        │
        ├── normalize_latency(ms)   → 1.0 at ≤500ms, 0.0 at ≥10s
        ├── normalize_cost(usd)       → 1.0 at ≤$0.001, 0.0 at ≥$0.10
        │
        └── compute_composite_score(weights)
              └── weighted sum (default 0.2 each dimension)
```

Hallucination is inverted before weighting: `1 - raw_hallucination_rate`.

## 4. Agent Plugin System

```python
class BaseAgent(ABC):
    def register_tracer(self, tracer: AgentTracer): ...
    async def execute(self, task: str) -> AgentResult: ...
```

| Plugin | Purpose |
|--------|---------|
| `MockAgent` | Zero API keys; deterministic demo runs |
| `LangGraphAgent` | StateGraph: reasoning → tool_call → output |

Registration in `AGENT_REGISTRY` + `AGENT_METADATA` exposes plugins via `/api/agents`.

## 5. Kafka Event Schema

Topic: `eval-events` (configurable via `KAFKA_TOPIC_EVAL_EVENTS`)

```json
{
  "timestamp": "2026-06-23T12:00:00.000Z",
  "event_type": "agent_step",
  "payload": {
    "run_id": "uuid",
    "step": {
      "id": "uuid",
      "run_id": "uuid",
      "step_index": 0,
      "step_type": "reasoning | tool_call | memory_read | output",
      "content": "step content text",
      "tool_name": "optional",
      "tool_input": {},
      "tool_output": {},
      "duration_ms": 120,
      "timestamp": "2026-06-23T12:00:00.000Z"
    }
  }
}
```

Additional event types may include `run_started`, `run_completed`, `run_failed` in future versions.

## 6. Deployment

Docker Compose orchestrates Zookeeper, Kafka, backend, and frontend. The backend seeds 10 mock runs and 2 benchmarks on first startup for a populated dashboard.
