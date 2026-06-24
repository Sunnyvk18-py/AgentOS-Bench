"""Agent plugin registry with auto-discovery."""

import logging
import threading
from typing import Any

from app.agents.base import AgentResult, BaseAgent
from app.agents.langgraph_agent import LangGraphAgent
from app.agents.mock_agent import MockAgent
from app.core.agent_discovery import discover_agents
from app.core.agent_events import agent_event_bus

logger = logging.getLogger(__name__)

_registry_lock = threading.RLock()
AGENT_REGISTRY: dict[str, type[BaseAgent]] = {}
AGENT_METADATA: dict[str, dict[str, Any]] = {}


def reload_agents() -> tuple[set[str], set[str]]:
    """Reload agent registry from disk. Returns (added, removed) agent names."""
    registry, metadata = discover_agents()
    with _registry_lock:
        old_names = set(AGENT_REGISTRY.keys())
        AGENT_REGISTRY.clear()
        AGENT_REGISTRY.update(registry)
        AGENT_METADATA.clear()
        AGENT_METADATA.update(metadata)
        new_names = set(AGENT_REGISTRY.keys())
    added = new_names - old_names
    removed = old_names - new_names
    return added, removed


def on_agents_changed() -> None:
    added, removed = reload_agents()
    for name in added:
        meta = AGENT_METADATA.get(name, {})
        agent_event_bus.publish_sync(
            "agent_registered",
            {
                "name": name,
                "description": meta.get("description", ""),
                "config_schema": meta.get("config_schema", {}),
                "is_built_in": meta.get("is_built_in", False),
            },
        )
    for name in removed:
        agent_event_bus.publish_sync("agent_removed", {"name": name})


def get_agent_registry() -> dict[str, type[BaseAgent]]:
    with _registry_lock:
        return dict(AGENT_REGISTRY)


def get_agent_metadata() -> dict[str, dict[str, Any]]:
    with _registry_lock:
        return dict(AGENT_METADATA)


# Initial load
reload_agents()

__all__ = [
    "BaseAgent",
    "AgentResult",
    "MockAgent",
    "LangGraphAgent",
    "AGENT_REGISTRY",
    "AGENT_METADATA",
    "reload_agents",
    "on_agents_changed",
    "get_agent_registry",
    "get_agent_metadata",
]
