# AgentOS Bench

> Open-source LLM agent evaluation & observability framework.  
> **Plug in any agent. Benchmark any model. Know if it actually works.**

AgentOS Bench lets developers connect any AI agent (LangGraph, CrewAI, AutoGen, or custom), run evaluations, compare models side-by-side, and inspect step-by-step traces — all from a production-grade dashboard or CLI.

**Repository:** [github.com/Sunnyvk18-py/AgentOS-Bench](https://github.com/Sunnyvk18-py/AgentOS-Bench)

---

## What We Built

A full-stack evaluation platform with:

| Layer | What's included |
|-------|-----------------|
| **Backend** | FastAPI API, async SQLAlchemy + SQLite, Kafka event pipeline, eval engine, scoring, LLM-as-judge |
| **Frontend** | React 18 dashboard — stats, runs table, trace viewer, benchmark comparison, report export |
| **Agents** | Plugin system with **auto-discovery**, hot-reload, validate/register API, and upload UI |
| **CLI** | `agentbench` — run evals, benchmarks, reports, and manage agents from the terminal |
| **Infra** | Docker Compose (Kafka + app), GitHub Actions CI, seed data, E2E smoke tests |

Anyone can drop in a Python agent file, and within seconds it appears in the dashboard — no server restart required.

---

## Features

- **Plug-and-play agents** — inherit `BaseAgent`, implement `execute()`, auto-discovered from `backend/app/agents/`
- **Three ways to register agents** — drop a file, CLI upload, or dashboard upload modal
- **Multi-LLM benchmarking** — GPT-4o, Claude, Llama, DeepSeek, mock-model on identical tasks
- **Live trace viewer** — step-by-step reasoning, tool calls, latency per step
- **Composite scoring** — accuracy, hallucination, tool precision, latency, cost (weighted)
- **Real-time UI** — SSE agent registry updates; polling for in-progress eval runs
- **Kafka streaming** — eval events pipeline (gracefully degrades if Kafka is down)
- **LLM-as-judge** — hallucination detection via Anthropic API + heuristic fallback
- **Reports** — export JSON or Markdown for CI/CD
- **Mock agent** — works with **zero API keys** out of the box
- **Seeded demo data** — 10 eval runs + 2 benchmarks on first startup

---

## Quickstart

### Docker (recommended)

```bash
git clone https://github.com/Sunnyvk18-py/AgentOS-Bench
cd AgentOS-Bench
cp backend/.env.example backend/.env
# Optional: add OPENAI_API_KEY, ANTHROPIC_API_KEY to backend/.env
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/health |
| API docs | http://localhost:8000/docs |

On first boot, `seed.py` populates the dashboard with sample runs and benchmarks.

### Local development

**Backend**
```bash
cd backend
pip install -r requirements.txt
python seed.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**CLI**
```bash
cd backend
pip install -e .
agentbench status
```

---

## Dashboard

| Page | Description |
|------|-------------|
| **Dashboard** | KPI cards, score trend chart, model comparison, recent runs, **live registered agents grid** |
| **Eval Runs** | Sortable/filterable table, status badges, bulk delete, CSV export, new run modal |
| **Run Detail** | Score breakdown, live trace timeline, JSON/Markdown report download |
| **Benchmark** | Multi-model comparison table, radar chart, benchmark history with winner badges |
| **Reports** | Select a run, preview and download JSON or Markdown |

Dark theme UI built with Tailwind CSS, TanStack Table, TanStack Query, and Recharts.

---

## Adding Your Own Agent

### Option A — Drop a file (zero config)

```bash
cp my_agent.py backend/app/agents/
# Auto-discovered within ~2 seconds. No restart needed.
```

### Option B — CLI

```bash
pip install -e backend/
agentbench agents add ./my_agent.py
agentbench agents list
```

### Option C — UI

Click **Upload Agent** on the dashboard or in the **New Eval Run** modal.  
Drag & drop a `.py` file → validate → register.

### Agent template

Copy [`backend/app/agents/TEMPLATE.py`](backend/app/agents/TEMPLATE.py) and implement `execute()`.

```python
from app.agents.base import AgentResult, BaseAgent


class MyAgent(BaseAgent):
    __agent_name__ = "my_agent"
    __agent_description__ = "Does something useful"
    __agent_config_schema__ = {
        "temperature": {"type": "float", "default": 0.7},
    }

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.7, **kwargs):
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature

    async def execute(self, task: str) -> AgentResult:
        # Record steps for the trace viewer
        if self.tracer:
            self.tracer.record_step(
                step_type="reasoning",
                content=f"Planning: {task[:120]}",
                duration_ms=100,
            )

        output = f"Completed: {task}"

        if self.tracer:
            self.tracer.record_step(step_type="output", content=output, duration_ms=50)

        return AgentResult(
            output=output,
            tools_used=["search_kb"],
            total_tokens=350,
            cost_usd=0.0012,
        )
```

**Requirements:**
- Inherit from `BaseAgent`
- Implement `async execute(task) -> AgentResult`
- Set `__agent_name__`, `__agent_description__`, optional `__agent_config_schema__`
- Call `self.tracer.record_step()` for live trace timeline
- Return `tools_used` for tool precision scoring

**Built-in agents:** `mock` (no API keys), `langgraph` (LangGraph StateGraph plugin)

---

## CLI Reference (`agentbench`)

Install: `pip install -e backend/`

Global option: `--api-url` (default: `http://localhost:8000`, or `AGENTBENCH_API_URL`)

```bash
# Setup
agentbench init                          # interactive .env wizard
agentbench status                        # API, DB, Kafka, agent count, runs today

# Agents
agentbench agents list                   # table of registered agents
agentbench agents add ./my_agent.py      # validate + copy to agents/

# Eval runs
agentbench run \
  --agent mock \
  --model gpt-4o \
  --task "Summarize Q4 sales report" \
  --watch                                # live trace polling

# Benchmarks
agentbench benchmark \
  --name "Sales Summary Showdown" \
  --task "Summarize Q4 sales and list top 3 products" \
  --models gpt-4o,claude-3-5-sonnet,mock-model \
  --agent mock

# Reports
agentbench report --run-id <uuid> --format markdown
agentbench report --run-id <uuid> --format json --output report.json
```

---

## API Reference

All responses use envelope: `{ "success": bool, "data": ..., "error": str | null }`

### Eval runs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/runs` | Trigger new eval run (background) |
| `GET` | `/api/runs` | List runs (paginated, filterable) |
| `GET` | `/api/runs/{id}` | Single run with steps |
| `DELETE` | `/api/runs/{id}` | Delete run |
| `GET` | `/api/runs/{id}/steps` | Steps only |
| `GET` | `/api/runs/{id}/score` | Score breakdown |

### Benchmarks
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/benchmarks` | Trigger multi-model benchmark |
| `GET` | `/api/benchmarks` | List all benchmarks |
| `GET` | `/api/benchmarks/{id}` | Single benchmark with results matrix |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List registered agents |
| `GET` | `/api/agents/stream` | SSE live registry updates |
| `POST` | `/api/agents/validate` | Validate agent source code |
| `POST` | `/api/agents/register` | Save agent file + hot-reload |
| `GET` | `/api/agents/{name}` | Agent details + config schema |

### Reports & stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/reports/export` | Generate JSON or Markdown report |
| `GET` | `/api/reports/{run_id}` | Cached report |
| `GET` | `/api/stats` | Dashboard KPIs and charts data |
| `GET` | `/health` | API, DB, Kafka status + agent count |

---

## Metrics Explained

| Metric | Description | Range |
|--------|-------------|-------|
| **Accuracy** | Token overlap + semantic similarity vs expected output | 0–1 |
| **Hallucination** | LLM-as-judge score (inverted in composite) | 0–1 |
| **Tool Precision** | F1 score on expected vs actual tool usage | 0–1 |
| **Latency** | Normalized; 1.0 = ≤500ms, 0.0 = ≥10s | 0–1 |
| **Cost** | Normalized; 1.0 = ≤$0.001, 0.0 = ≥$0.10 | 0–1 |
| **Composite** | Weighted average of all five (default 0.2 each) | **0–1** |

Scores display as percentages in the UI (e.g. 89.0%).

---

## Project Structure

```
AgentOS-Bench/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + lifespan
│   │   ├── agents/                 # Plugin directory (auto-discovered)
│   │   │   ├── TEMPLATE.py         # Copy this to create your agent
│   │   │   ├── mock_agent.py       # Built-in demo agent
│   │   │   └── langgraph_agent.py  # LangGraph plugin
│   │   ├── api/                    # REST routes
│   │   ├── core/                   # EvalRunner, scoring, Kafka, discovery
│   │   ├── models/                 # SQLAlchemy ORM
│   │   └── schemas/                # Pydantic v2 schemas
│   ├── agentbench/                 # CLI package (agentbench command)
│   ├── tests/                      # pytest + E2E smoke test
│   ├── seed.py                     # Demo data seeder
│   ├── setup.py                    # pip install -e .
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── routes/                 # Dashboard, runs, benchmark, reports
│       ├── components/             # UI components + agent upload
│       └── hooks/                  # TanStack Query + SSE agent stream
├── docker-compose.yml              # Kafka + Zookeeper + backend + frontend
├── .github/workflows/ci.yml        # Lint, test, build
├── architecture.md                 # System design deep-dive
├── CONTRIBUTING.md
└── assets/                         # Dashboard screenshots
```

---

## Architecture

```
User → React Dashboard / CLI
         ↓ REST + SSE
       FastAPI API
         ↓
    EvalRunner → Agent Plugin → AgentTracer
         ↓              ↓
    Scoring         Kafka (eval events)
         ↓              ↓
    SQLite DB ← Kafka Consumer
```

See [architecture.md](architecture.md) for data flow, scoring pipeline, Kafka event schema, and plugin design.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./agentos_bench.db` | Async SQLite connection |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `KAFKA_TOPIC_EVAL_EVENTS` | `eval-events` | Eval event topic |
| `OPENAI_API_KEY` | — | Optional; for OpenAI models |
| `ANTHROPIC_API_KEY` | — | Optional; for LLM-as-judge + Claude |
| `USE_SEMANTIC_SCORING` | `false` | Enable sentence-transformers accuracy |
| `ENV` | `dev` | `dev` enables CORS for all origins |
| `LOG_LEVEL` | `INFO` | Logging level |

The **mock agent works without any API keys**.

---

## Development & Testing

```bash
# Backend tests (15 tests)
cd backend
pip install -r requirements.txt
pytest tests/ -v

# E2E API smoke test (server must be running)
python tests/e2e_smoke.py

# Frontend
cd frontend
npm run lint
npm run build

# Code quality
cd backend
ruff check .
black --check .
```

CI runs on every push to `main` via GitHub Actions: Ruff, Black, pytest, ESLint, TypeScript, Vite build, Docker build.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, LangGraph, SQLAlchemy async, Kafka, Uvicorn |
| **Frontend** | React 18, TypeScript, Vite, TanStack Table/Query, Recharts, Tailwind CSS |
| **CLI** | Click, Rich, httpx |
| **Infra** | Docker Compose, GitHub Actions, SQLite, confluent-kafka |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code standards, and how to add agent plugins.

---

## License

MIT — see [LICENSE](LICENSE).
