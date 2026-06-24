from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.tracer import AgentTracer


@dataclass
class AgentResult:
    output: str
    steps: list[dict] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    total_tokens: int = 0
    cost_usd: float = 0.0


class BaseAgent(ABC):
    def __init__(self) -> None:
        self.tracer: AgentTracer | None = None

    def register_tracer(self, tracer: AgentTracer) -> None:
        self.tracer = tracer

    @abstractmethod
    async def execute(self, task: str) -> AgentResult:
        pass
