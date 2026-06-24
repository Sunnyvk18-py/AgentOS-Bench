# AgentOS Bench

> Open-source LLM agent evaluation & observability framework. 
> Plug in any agent. Benchmark any model. Know if it actually works.

## Features
- Plug-and-play agent evaluation via a simple abstract interface
- Multi-LLM benchmarking: GPT-4o, Claude, Llama, DeepSeek side-by-side
- Real-time trace viewer with step-by-step agent reasoning timeline
- Composite scoring: accuracy + hallucination + tool precision + latency + cost
- Kafka-powered streaming eval event pipeline
- LLM-as-judge hallucination detection
- CI/CD ready: JSON/Markdown report export + GitHub Actions integration
- Production-grade FastAPI backend + React dashboard

## Quickstart
```bash
git clone https://github.com/Sunnyvk18-py/AgentOS-Bench
cd AgentOS-Bench
cp backend/.env.example backend/.env
# Add your API keys to .env (optional — mock agent works without keys)
docker-compose up --build
```

Visit http://localhost:3000

## Architecture
See [architecture.md](architecture.md) for full system diagram.

## Adding Your Own Agent

### Option A — Drop a file (zero config)
```bash
cp my_agent.py backend/app/agents/
# That's it. Auto-discovered. No restart needed.
```

### Option B — CLI
```bash
pip install -e backend/
agentbench agents add ./my_agent.py
```

### Option C — UI
Click **Upload Agent** on the dashboard or in the New Eval Run modal.

### Agent Template
Copy `backend/app/agents/TEMPLATE.py` and implement `execute()`.
The only requirement: return an `AgentResult`.

```python
class MyAgent(BaseAgent):
    __agent_name__ = "my_agent"
    __agent_description__ = "Does something useful"

    async def execute(self, task: str) -> AgentResult:
        result = await my_logic(task)
        return AgentResult(output=result, tools_used=[], 
                          total_tokens=100, cost_usd=0.001)
```

### CLI Quick Reference
```bash
agentbench agents list              # see all registered agents
agentbench run --agent my_agent --model gpt-4o --task "your task"
agentbench benchmark --name "Test" --task "your task" --models gpt-4o,claude-3-5-sonnet --agent my_agent
agentbench report --run-id abc123 --format markdown
agentbench status                   # health check
```

## Metrics Explained
| Metric | Description | Range |
|--------|-------------|-------|
| Accuracy | Token overlap + semantic similarity vs expected output | 0–1 |
| Hallucination | LLM-as-judge score (inverted) | 0–1 |
| Tool Precision | F1 score on tool usage | 0–1 |
| Latency | Normalized, 1.0 = <500ms | 0–1 |
| Cost | Normalized, 1.0 = <$0.001 | 0–1 |
| **Composite** | Weighted average (configurable) | **0–1** |

## Tech Stack
Backend: Python, FastAPI, Pydantic v2, LangGraph, SQLAlchemy, Kafka
Frontend: React, TypeScript, TanStack Table, Recharts, Tailwind CSS

## License
MIT
