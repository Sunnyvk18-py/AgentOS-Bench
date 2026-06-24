import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import success_response
from app.core.benchmark_harness import BenchmarkHarness
from app.database import AsyncSessionLocal, get_db
from app.models.run import BenchmarkResult
from app.schemas.run import BenchmarkRequest, BenchmarkResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


async def _run_benchmark_task(request: BenchmarkRequest) -> None:
    async with AsyncSessionLocal() as session:
        try:
            harness = BenchmarkHarness(session)
            await harness.run_benchmark(request)
        except Exception as exc:
            logger.exception("Background benchmark failed: %s", exc)


@router.post("")
async def create_benchmark(
    payload: BenchmarkRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    try:
        background_tasks.add_task(_run_benchmark_task, payload)
        return success_response(
            {
                "benchmark_name": payload.benchmark_name,
                "status": "running",
                "models": payload.models,
            }
        )
    except Exception as exc:
        logger.exception("Failed to create benchmark: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("")
async def list_benchmarks(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        result = await db.execute(
            select(BenchmarkResult).order_by(BenchmarkResult.created_at.desc())
        )
        benchmarks = result.scalars().all()
        return success_response(
            [BenchmarkResponse.model_validate(b).model_dump() for b in benchmarks]
        )
    except Exception as exc:
        logger.exception("Failed to list benchmarks: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{benchmark_id}")
async def get_benchmark(benchmark_id: str, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        result = await db.execute(
            select(BenchmarkResult).where(BenchmarkResult.id == benchmark_id)
        )
        benchmark = result.scalar_one_or_none()
        if not benchmark:
            raise HTTPException(status_code=404, detail="Benchmark not found")
        return success_response(BenchmarkResponse.model_validate(benchmark).model_dump())
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get benchmark: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
