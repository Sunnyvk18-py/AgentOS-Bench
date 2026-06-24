import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agents import get_agent_metadata, get_agent_registry, on_agents_changed
from app.api.responses import success_response
from app.core.agent_discovery import (
    AGENTS_DIR,
    safe_agent_filename,
    validate_agent_source,
)
from app.core.agent_events import agent_event_bus, format_sse
from app.schemas.agent import (
    AgentRegisterRequest,
    AgentValidateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


def _list_agents_payload() -> list[dict[str, Any]]:
    registry = get_agent_registry()
    metadata = get_agent_metadata()
    agents = []
    for name in registry:
        meta = metadata.get(name, {})
        agents.append(
            {
                "name": name,
                "description": meta.get("description", ""),
                "config_schema": meta.get("config_schema", {}),
                "is_built_in": meta.get("is_built_in", name in ("mock", "langgraph")),
            }
        )
    return sorted(agents, key=lambda a: a["name"])


@router.get("")
async def list_agents() -> dict[str, Any]:
    return success_response(_list_agents_payload())


@router.get("/stream")
async def stream_agents() -> StreamingResponse:
    async def event_generator():
        queue = await agent_event_bus.subscribe()
        try:
            yield format_sse({"event": "snapshot", "payload": {"agents": _list_agents_payload()}})
            while True:
                event = await queue.get()
                yield format_sse(event)
        finally:
            await agent_event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/validate")
async def validate_agent(payload: AgentValidateRequest) -> dict[str, Any]:
    try:
        result = validate_agent_source(payload.content)
        return success_response(result)
    except Exception as exc:
        logger.exception("Agent validation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/register")
async def register_agent(payload: AgentRegisterRequest) -> dict[str, Any]:
    try:
        validation = validate_agent_source(payload.content)
        if not validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail={"errors": validation.get("errors", ["Invalid agent file"])},
            )

        filename = safe_agent_filename(payload.filename)
        target = AGENTS_DIR / filename
        if target.exists():
            raise HTTPException(status_code=409, detail=f"Agent file '{filename}' already exists")

        target.write_text(payload.content, encoding="utf-8")
        on_agents_changed()
        agent_name = validation.get("agent_name") or filename.replace(".py", "")

        return success_response(
            {
                "filename": filename,
                "agent_name": agent_name,
                "message": f"Agent '{agent_name}' registered. Hot-reload picked it up automatically.",
            }
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Agent registration failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{name}")
async def get_agent(name: str) -> dict[str, Any]:
    registry = get_agent_registry()
    metadata = get_agent_metadata()
    if name not in registry:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    meta = metadata.get(name, {})
    return success_response(
        {
            "name": name,
            "description": meta.get("description", ""),
            "config_schema": meta.get("config_schema", {}),
            "is_built_in": meta.get("is_built_in", False),
            "available": True,
        }
    )
