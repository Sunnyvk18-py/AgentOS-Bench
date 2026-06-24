import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import agents, benchmark, reports, runs
from app.config import get_settings
from app.agents import on_agents_changed
from app.core.agent_watcher import AgentWatcher
from app.core.kafka_consumer import kafka_consumer
from app.core.kafka_producer import kafka_producer
from app.database import create_all_tables, engine

logging.basicConfig(
    level=get_settings().LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()
agent_watcher = AgentWatcher(on_change=on_agents_changed)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AgentOS Bench API (env=%s)", settings.ENV)
    await create_all_tables()
    on_agents_changed()
    agent_watcher.start()
    await kafka_consumer.start()
    yield
    agent_watcher.stop()
    await kafka_consumer.stop()
    kafka_producer.flush()
    await engine.dispose()
    logger.info("AgentOS Bench API shutdown complete")


app = FastAPI(
    title="AgentOS Bench",
    description="LLM Agent Evaluation & Observability Framework",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "dev" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs.router, prefix="/api")
app.include_router(benchmark.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "error": str(exc)},
    )


@app.get("/health")
async def health_check() -> dict[str, Any]:
    db_ok = False
    kafka_ok = kafka_producer._available

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception as exc:
        logger.warning("Health check DB failed: %s", exc)

    from app.agents import get_agent_registry
    from sqlalchemy import func, select
    from app.database import AsyncSessionLocal
    from app.models.run import EvalRun

    agents_count = len(get_agent_registry())
    completed_runs_today = 0
    try:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        async with AsyncSessionLocal() as session:
            completed_runs_today = (
                await session.execute(
                    select(func.count()).select_from(EvalRun).where(
                        EvalRun.status == "completed",
                        EvalRun.completed_at >= today_start,
                    )
                )
            ).scalar() or 0
    except Exception as exc:
        logger.warning("Health check runs count failed: %s", exc)

    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "disconnected",
        "kafka": "connected" if kafka_ok else "unavailable",
        "agents_count": agents_count,
        "completed_runs_today": completed_runs_today,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/stats")
async def dashboard_stats() -> dict[str, Any]:
    from sqlalchemy import func, select

    from app.database import AsyncSessionLocal
    from app.models.run import EvalRun

    async with AsyncSessionLocal() as session:
        total_runs = (await session.execute(select(func.count()).select_from(EvalRun))).scalar() or 0
        avg_score = (
            await session.execute(select(func.avg(EvalRun.composite_score)))
        ).scalar()
        avg_latency = (
            await session.execute(select(func.avg(EvalRun.latency_ms)))
        ).scalar()
        total_cost = (
            await session.execute(select(func.sum(EvalRun.cost_usd)))
        ).scalar()

        recent = await session.execute(
            select(EvalRun).order_by(EvalRun.created_at.desc()).limit(30)
        )
        runs_list = recent.scalars().all()

        model_scores: dict[str, list[float]] = {}
        for run in runs_list:
            if run.composite_score is not None:
                model_scores.setdefault(run.llm_model, []).append(run.composite_score)

        model_avg = {
            model: sum(scores) / len(scores) for model, scores in model_scores.items()
        }

        return {
            "success": True,
            "data": {
                "total_runs": total_runs,
                "avg_composite_score": float(avg_score or 0),
                "avg_latency_ms": float(avg_latency or 0),
                "total_cost_usd": float(total_cost or 0),
                "score_trend": [
                    {"run_id": r.id, "composite_score": r.composite_score, "created_at": r.created_at.isoformat()}
                    for r in reversed(runs_list)
                    if r.composite_score is not None
                ],
                "model_comparison": model_avg,
                "recent_runs": [
                    {
                        "id": r.id,
                        "agent_name": r.agent_name,
                        "llm_model": r.llm_model,
                        "status": r.status,
                        "composite_score": r.composite_score,
                        "created_at": r.created_at.isoformat(),
                    }
                    for r in runs_list[:5]
                ],
            },
            "error": None,
        }
