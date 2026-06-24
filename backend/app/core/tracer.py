import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class AgentTracer:
    """Captures step-by-step agent execution traces."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self._steps: list[dict[str, Any]] = []
        self._started = False
        self._ended = False

    def start_trace(self) -> None:
        self._started = True
        logger.debug("Trace started for run %s", self.run_id)

    def record_step(
        self,
        step_type: str,
        content: str,
        tool_name: str | None = None,
        tool_input: dict | None = None,
        tool_output: dict | None = None,
        duration_ms: int = 0,
    ) -> None:
        if not self._started:
            self.start_trace()

        step = {
            "id": str(uuid.uuid4()),
            "run_id": self.run_id,
            "step_index": len(self._steps),
            "step_type": step_type,
            "content": content,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._steps.append(step)
        logger.debug("Recorded step %d (%s) for run %s", step["step_index"], step_type, self.run_id)

    def end_trace(self) -> None:
        self._ended = True
        logger.debug("Trace ended for run %s with %d steps", self.run_id, len(self._steps))

    def get_steps(self) -> list[dict[str, Any]]:
        return list(self._steps)

    def total_latency_ms(self) -> int:
        return sum(step.get("duration_ms", 0) for step in self._steps)
