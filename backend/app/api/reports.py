import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.responses import success_response
from app.database import get_db
from app.models.run import EvalRun
from app.schemas.run import ReportRequest
from app.utils.report_generator import ReportGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])

_report_cache: dict[str, dict] = {}
_generator = ReportGenerator()


@router.post("/export")
async def export_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    try:
        result = await db.execute(
            select(EvalRun).options(selectinload(EvalRun.steps)).where(EvalRun.id == payload.run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        steps = sorted(run.steps, key=lambda s: s.step_index)

        if payload.format == "markdown":
            content = _generator.generate_markdown_report(run, steps)
            _report_cache[payload.run_id] = {"format": "markdown", "content": content}
            return PlainTextResponse(content, media_type="text/markdown")

        report = _generator.generate_json_report(run, steps)
        _report_cache[payload.run_id] = {"format": "json", "content": report}
        return JSONResponse(content=success_response(report))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to export report: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{run_id}")
async def get_cached_report(run_id: str) -> dict[str, Any]:
    cached = _report_cache.get(run_id)
    if not cached:
        raise HTTPException(status_code=404, detail="No cached report for this run")
    return success_response(cached)
