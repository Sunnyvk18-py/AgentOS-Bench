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
```python
from app.agents.base import BaseAgent, AgentResult

class MyAgent(BaseAgent):
    async def execute(self, task: str) -> AgentResult:
        # your agent logic here
        return AgentResult(output=..., steps=..., 
                          tools_used=..., total_tokens=..., cost_usd=...)
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
