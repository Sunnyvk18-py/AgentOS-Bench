import asyncio
import hashlib
import logging
import random
from typing import Any

from app.agents.base import AgentResult, BaseAgent

logger = logging.getLogger(__name__)


class MockAgent(BaseAgent):
    """Mock agent for testing without real LLM calls."""

    def __init__(
        self,
        model_name: str = "mock-model",
        error_rate: float = 0.0,
        step_count: int = 4,
        **_: Any,
    ) -> None:
        super().__init__()
        self.model_name = model_name
        self.error_rate = error_rate
        self.step_count = max(3, min(5, step_count))

    async def execute(self, task: str) -> AgentResult:
        if random.random() < self.error_rate:
            raise RuntimeError("Mock agent simulated failure")

        steps: list[dict] = []
        tools_used: list[str] = []
        tool_step_index = random.randint(1, self.step_count - 1)

        for i in range(self.step_count):
            await asyncio.sleep(0.05)
            duration_ms = random.randint(50, 200)

            if i == tool_step_index:
                tool_name = "search_database"
                tool_input = {"query": task[:50]}
                tool_output = {"results": ["result_a", "result_b"]}
                content = f"Calling tool {tool_name} to gather information for: {task[:80]}"
                step_type = "tool_call"
                tools_used.append(tool_name)

                if self.tracer:
                    self.tracer.record_step(
                        step_type=step_type,
                        content=content,
                        tool_name=tool_name,
                        tool_input=tool_input,
                        tool_output=tool_output,
                        duration_ms=duration_ms,
                    )
                steps.append(
                    {
                        "step_type": step_type,
                        "content": content,
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                        "tool_output": tool_output,
                        "duration_ms": duration_ms,
                    }
                )
            else:
                step_type = "reasoning" if i < self.step_count - 1 else "output"
                content = (
                    f"Step {i + 1}: Analyzing task context — {task[:60]}..."
                    if step_type == "reasoning"
                    else f"Final answer for task: {self._deterministic_output(task)}"
                )
                if self.tracer:
                    self.tracer.record_step(
                        step_type=step_type,
                        content=content,
                        duration_ms=duration_ms,
                    )
                steps.append(
                    {
                        "step_type": step_type,
                        "content": content,
                        "duration_ms": duration_ms,
                    }
                )

        output = self._deterministic_output(task)
        total_tokens = sum(len(s["content"].split()) for s in steps) * 2
        cost_usd = total_tokens * 0.000002

        return AgentResult(
            output=output,
            steps=steps,
            tools_used=tools_used,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
        )

    @staticmethod
    def _deterministic_output(task: str) -> str:
        digest = hashlib.sha256(task.encode()).hexdigest()[:8]
        return f"MockAgent completed task with reference ID {digest}. Summary: {task[:100]}"
