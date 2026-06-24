import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AGENT_REGISTRY
from app.core.eval_runner import EvalRunner
from app.models.run import BenchmarkResult
from app.schemas.run import BenchmarkRequest, BenchmarkResponse

logger = logging.getLogger(__name__)


class BenchmarkHarness:
    """Multi-LLM benchmark engine."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.eval_runner = EvalRunner(session)

    async def run_benchmark(self, request: BenchmarkRequest) -> BenchmarkResponse:
        results: dict[str, dict[str, Any]] = {}
        winner_model = request.models[0]
        highest_score = -1.0

        agent_cls = AGENT_REGISTRY.get(request.agent_name)
        if agent_cls is None:
            raise ValueError(f"Unknown agent: {request.agent_name}")

        agent_config = request.agent_config or {}

        for model in request.models:
            logger.info("Benchmarking model %s for task: %s", model, request.benchmark_name)
            run = await self.eval_runner.create_pending_run(
                agent_name=request.agent_name,
                llm_model=model,
                task_description=request.task_description,
            )
            agent = agent_cls(model_name=model, **agent_config)
            completed_run = await self.eval_runner.run(
                run_id=run.id,
                agent=agent,
                task=request.task_description,
                llm_model=model,
            )
            results[model] = {
                "accuracy": completed_run.accuracy_score,
                "hallucination": completed_run.hallucination_score,
                "latency_ms": completed_run.latency_ms,
                "cost_usd": completed_run.cost_usd,
                "composite_score": completed_run.composite_score,
                "run_id": completed_run.id,
            }
            score = completed_run.composite_score or 0.0
            if score > highest_score:
                highest_score = score
                winner_model = model

        benchmark = BenchmarkResult(
            id=str(uuid.uuid4()),
            benchmark_name=request.benchmark_name,
            task_description=request.task_description,
            models_compared=request.models,
            results=results,
            winner_model=winner_model,
        )
        self.session.add(benchmark)
        await self.session.commit()
        await self.session.refresh(benchmark)

        return BenchmarkResponse.model_validate(benchmark)
