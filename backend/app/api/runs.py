import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents import AGENT_REGISTRY
from app.api.responses import error_response, success_response
from app.core.eval_runner import EvalRunner
from app.database import AsyncSessionLocal, get_db
from app.models.run import AgentStep, EvalRun
from app.schemas.run import AgentStepResponse, EvalRunCreate, EvalRunResponse, ScoreBreakdown

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/runs", tags=["runs"])


async def _execute_run(run_id: str, payload: EvalRunCreate) -> None:
    async with AsyncSessionLocal() as session:
        try:
            agent_cls = AGENT_REGISTRY.get(payload.agent_name)
            if agent_cls is None:
                raise ValueError(f"Unknown agent: {payload.agent_name}")
            agent_config = payload.agent_config or {}
            agent = agent_cls(model_name=payload.llm_model, **agent_config)
            runner = EvalRunner(session)
            await runner.run(
                run_id=run_id,
                agent=agent,
                task=payload.task_description,
                llm_model=payload.llm_model,
            )
        except Exception as exc:
            logger.exception("Background eval run failed: %s", exc)


@router.post("")
async def create_run(
    payload: EvalRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        if payload.agent_name not in AGENT_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {payload.agent_name}")

        runner = EvalRunner(db)
        run = await runner.create_pending_run(
            agent_name=payload.agent_name,
            llm_model=payload.llm_model,
            task_description=payload.task_description,
        )
        background_tasks.add_task(_execute_run, run.id, payload)
        return success_response(EvalRunResponse.model_validate(run).model_dump())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create run: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("")
async def list_runs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    try:
        query = select(EvalRun).order_by(EvalRun.created_at.desc())
        count_query = select(func.count()).select_from(EvalRun)

        if status:
            query = query.where(EvalRun.status == status)
            count_query = count_query.where(EvalRun.status == status)
        if model:
            query = query.where(EvalRun.llm_model == model)
            count_query = count_query.where(EvalRun.llm_model == model)

        total = (await db.execute(count_query)).scalar() or 0
        offset = (page - 1) * page_size
        result = await db.execute(query.offset(offset).limit(page_size))
        runs = result.scalars().all()

        return success_response(
            {
                "items": [EvalRunResponse.model_validate(r).model_dump() for r in runs],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )
    except Exception as exc:
        logger.exception("Failed to list runs: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{run_id}")
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        result = await db.execute(
            select(EvalRun).options(selectinload(EvalRun.steps)).where(EvalRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        response = EvalRunResponse.model_validate(run)
        return success_response(response.model_dump())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get run: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/{run_id}")
async def delete_run(run_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        result = await db.execute(select(EvalRun).where(EvalRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        await db.execute(delete(EvalRun).where(EvalRun.id == run_id))
        await db.commit()
        return success_response({"deleted": run_id})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to delete run: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{run_id}/steps")
async def get_run_steps(run_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        result = await db.execute(
            select(AgentStep)
            .where(AgentStep.run_id == run_id)
            .order_by(AgentStep.step_index)
        )
        steps = result.scalars().all()
        return success_response(
            [AgentStepResponse.model_validate(s).model_dump() for s in steps]
        )
    except Exception as exc:
        logger.exception("Failed to get steps: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{run_id}/score")
async def get_run_score(run_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        result = await db.execute(select(EvalRun).where(EvalRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        breakdown = ScoreBreakdown(
            composite_score=run.composite_score,
            accuracy_score=run.accuracy_score,
            hallucination_score=run.hallucination_score,
            tool_call_precision=run.tool_call_precision,
            latency_ms=run.latency_ms,
            cost_usd=run.cost_usd,
        )
        return success_response(breakdown.model_dump())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get score: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
