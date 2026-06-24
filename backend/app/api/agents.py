import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.agents import AGENT_METADATA, AGENT_REGISTRY
from app.api.responses import success_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("")
async def list_agents() -> dict[str, Any]:
    agents = []
    for name in AGENT_REGISTRY:
        meta = AGENT_METADATA.get(name, {})
        agents.append(
            {
                "name": name,
                "description": meta.get("description", ""),
                "config_schema": meta.get("config_schema", {}),
            }
        )
    return success_response(agents)


@router.get("/{name}")
async def get_agent(name: str) -> dict[str, Any]:
    if name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    meta = AGENT_METADATA.get(name, {})
    return success_response(
        {
            "name": name,
            "description": meta.get("description", ""),
            "config_schema": meta.get("config_schema", {}),
            "available": True,
        }
    )
