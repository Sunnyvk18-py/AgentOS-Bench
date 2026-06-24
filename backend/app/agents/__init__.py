"""Agent plugin implementations."""

from app.agents.base import AgentResult, BaseAgent
from app.agents.langgraph_agent import LangGraphAgent
from app.agents.mock_agent import MockAgent

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "mock": MockAgent,
    "langgraph": LangGraphAgent,
}

AGENT_METADATA: dict[str, dict] = {
    "mock": {
        "name": "mock",
        "description": "Built-in mock agent for testing without API keys",
        "config_schema": {
            "error_rate": {"type": "float", "default": 0.0, "description": "Simulated failure rate"},
            "step_count": {"type": "int", "default": 4, "description": "Number of reasoning steps"},
        },
    },
    "langgraph": {
        "name": "langgraph",
        "description": "LangGraph-based agent with reasoning and tool call nodes",
        "config_schema": {
            "system_prompt": {"type": "string", "default": "You are a helpful AI agent."},
            "tools": {"type": "array", "default": [], "description": "Optional tool definitions"},
        },
    },
}

__all__ = ["BaseAgent", "AgentResult", "MockAgent", "LangGraphAgent", "AGENT_REGISTRY", "AGENT_METADATA"]
