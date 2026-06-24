import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

VALID_AGENT = '''
from app.agents.base import AgentResult, BaseAgent

class DemoAgent(BaseAgent):
    __agent_name__ = "demo_agent"
    __agent_description__ = "Demo agent for tests"

    async def execute(self, task: str) -> AgentResult:
        return AgentResult(output=task, tools_used=[], total_tokens=1, cost_usd=0.0)
'''

INVALID_AGENT = '''
class NotAnAgent:
    async def execute(self, task: str):
        return task
'''


@pytest.mark.asyncio
async def test_list_agents_includes_builtins():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()["data"]
    names = {a["name"] for a in data}
    assert "mock" in names
    assert "langgraph" in names


@pytest.mark.asyncio
async def test_validate_agent_valid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/agents/validate", json={"content": VALID_AGENT})
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["valid"] is True
    assert result["agent_name"] == "demo_agent"


@pytest.mark.asyncio
async def test_validate_agent_invalid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/agents/validate", json={"content": INVALID_AGENT})
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["valid"] is False
    assert result["errors"]


@pytest.mark.asyncio
async def test_register_and_list_agent(tmp_path, monkeypatch):
    from app.core import agent_discovery

    monkeypatch.setattr(agent_discovery, "AGENTS_DIR", tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/agents/register",
            json={"filename": "demo_agent.py", "content": VALID_AGENT},
        )
    assert response.status_code == 200
    assert response.json()["data"]["agent_name"] == "demo_agent"
