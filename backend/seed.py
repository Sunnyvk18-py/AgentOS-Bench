import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from app.agents.mock_agent import MockAgent
from app.core.eval_runner import EvalRunner
from app.core.benchmark_harness import BenchmarkHarness
from app.database import AsyncSessionLocal, create_all_tables
from app.models.run import BenchmarkResult, EvalRun
from app.schemas.run import BenchmarkRequest

logger = logging.getLogger(__name__)

MODELS = ["gpt-4o", "claude-3-5-sonnet", "llama-3.1-8b", "deepseek-chat", "mock-model"]
TASKS = [
    "Summarize the quarterly sales report and identify top 3 products.",
    "Research competitor pricing and generate a comparison table.",
    "Extract key dates from the project timeline document.",
    "Answer customer support ticket about refund policy.",
    "Analyze log files for error patterns in the last 24 hours.",
    "Generate a meeting summary from transcript notes.",
    "Validate data quality in the uploaded CSV dataset.",
    "Create a step-by-step troubleshooting guide for API timeouts.",
    "Compare feature requests from two product feedback channels.",
    "Draft a technical architecture overview for a microservices migration.",
]


async def seed() -> None:
    await create_all_tables()

    async with AsyncSessionLocal() as session:
        from sqlalchemy import func, select

        existing = await session.execute(select(func.count()).select_from(EvalRun))
        count = existing.scalar() or 0
        if count >= 10:
            logger.info("Database already seeded with %d runs, skipping.", count)
            return

        runner = EvalRunner(session)
        base_time = datetime.now(timezone.utc)

        for i, task in enumerate(TASKS):
            model = MODELS[i % len(MODELS)]
            run = await runner.create_pending_run(
                agent_name="mock",
                llm_model=model,
                task_description=task,
            )
            agent = MockAgent(model_name=model, step_count=3 + (i % 3))
            await runner.run(
                run_id=run.id,
                agent=agent,
                task=task,
                llm_model=model,
            )
            run.created_at = base_time - timedelta(days=10 - i)
            await session.commit()

        harness = BenchmarkHarness(session)
        for bench_name, models in [
            ("Q4 Sales Analysis", ["gpt-4o", "claude-3-5-sonnet", "deepseek-chat"]),
            ("Support Ticket Triage", ["llama-3.1-8b", "mock-model", "gpt-4o"]),
        ]:
            request = BenchmarkRequest(
                benchmark_name=bench_name,
                task_description=f"Benchmark task: {bench_name}",
                models=models,
                agent_name="mock",
            )
            await harness.run_benchmark(request)

        logger.info("Seeded 10 eval runs and 2 benchmark results.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
