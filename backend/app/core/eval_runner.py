import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.config import get_settings
from app.core.kafka_producer import kafka_producer
from app.core.scoring import (
    compute_accuracy_score,
    compute_composite_score,
    compute_hallucination_score,
    compute_tool_precision,
)
from app.core.tracer import AgentTracer
from app.models.run import AgentStep, EvalRun
from app.schemas.run import ScoreWeights

logger = logging.getLogger(__name__)
settings = get_settings()


class EvalRunner:
    """Main evaluation orchestrator."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def run(
        self,
        run_id: str,
        agent: BaseAgent,
        task: str,
        llm_model: str,
        expected_output: str | None = None,
        expected_tools: list[str] | None = None,
        weights: ScoreWeights | None = None,
    ) -> EvalRun:
        try:
            result = await self.session.execute(select(EvalRun).where(EvalRun.id == run_id))
            run = result.scalar_one_or_none()
            if run is None:
                raise ValueError(f"EvalRun {run_id} not found")

            run.status = "running"
            await self.session.commit()

            tracer = AgentTracer(run_id)
            agent.register_tracer(tracer)
            tracer.start_trace()

            logger.info("Starting eval run %s with agent on model %s", run_id, llm_model)
            agent_result = await agent.execute(task)
            tracer.end_trace()

            steps = tracer.get_steps()
            for step_data in steps:
                step = AgentStep(
                    id=step_data["id"],
                    run_id=run_id,
                    step_index=step_data["step_index"],
                    step_type=step_data["step_type"],
                    content=step_data["content"],
                    tool_name=step_data.get("tool_name"),
                    tool_input=step_data.get("tool_input"),
                    tool_output=step_data.get("tool_output"),
                    duration_ms=step_data.get("duration_ms", 0),
                    timestamp=datetime.fromisoformat(step_data["timestamp"]),
                )
                self.session.add(step)
                await kafka_producer.produce_event(
                    settings.KAFKA_TOPIC_EVAL_EVENTS,
                    "agent_step",
                    {"run_id": run_id, "step": step_data},
                )

            expected = expected_output or task
            accuracy = compute_accuracy_score(expected, agent_result.output)
            hallucination = await compute_hallucination_score(agent_result.output, task)
            tool_precision = compute_tool_precision(
                expected_tools or ["search_database"],
                agent_result.tools_used,
            )
            latency_ms = tracer.total_latency_ms()
            composite = compute_composite_score(
                accuracy,
                hallucination,
                tool_precision,
                latency_ms,
                agent_result.cost_usd,
                weights,
            )

            run.status = "completed"
            run.composite_score = composite
            run.accuracy_score = accuracy
            run.hallucination_score = hallucination
            run.tool_call_precision = tool_precision
            run.latency_ms = latency_ms
            run.cost_usd = agent_result.cost_usd
            run.total_steps = len(steps)
            run.completed_at = datetime.now(timezone.utc)

            await self.session.commit()
            await self.session.refresh(run)
            logger.info("Eval run %s completed with composite score %.4f", run_id, composite)
            return run

        except Exception as exc:
            logger.exception("Eval run %s failed: %s", run_id, exc)
            try:
                result = await self.session.execute(select(EvalRun).where(EvalRun.id == run_id))
                run = result.scalar_one_or_none()
                if run:
                    run.status = "failed"
                    run.completed_at = datetime.now(timezone.utc)
                    await self.session.commit()
            except Exception as inner:
                logger.error("Failed to update run status: %s", inner)
            raise

    async def create_pending_run(
        self,
        agent_name: str,
        llm_model: str,
        task_description: str,
    ) -> EvalRun:
        run = EvalRun(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            llm_model=llm_model,
            task_description=task_description,
            status="pending",
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run
