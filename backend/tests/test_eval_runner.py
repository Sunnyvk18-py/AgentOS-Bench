import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.mock_agent import MockAgent
from app.core.eval_runner import EvalRunner
from app.models.run import EvalRun


@pytest.mark.asyncio
async def test_eval_runner_completes_mock_agent():
    session = AsyncMock()
    run = EvalRun(
        id="test-run-id",
        agent_name="mock",
        llm_model="mock-model",
        task_description="Test task",
        status="pending",
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = run
    session.execute = AsyncMock(return_value=mock_result)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()

    agent = MockAgent(model_name="mock-model")
    runner = EvalRunner(session)

    with patch.object(runner, "session", session):
        result = await runner.run(
            run_id="test-run-id",
            agent=agent,
            task="Test task for evaluation",
            llm_model="mock-model",
        )

    assert result.status == "completed"
    assert result.composite_score is not None
    assert result.total_steps is not None
    assert result.total_steps >= 3
