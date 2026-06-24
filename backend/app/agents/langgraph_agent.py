import asyncio
import logging
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.base import AgentResult, BaseAgent

logger = logging.getLogger(__name__)

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.000005, "output": 0.000015},
    "claude-3-5-sonnet": {"input": 0.000003, "output": 0.000015},
    "llama-3.1-8b": {"input": 0.0000001, "output": 0.0000001},
    "deepseek-chat": {"input": 0.000001, "output": 0.000002},
}


class AgentState(TypedDict):
    messages: list[str]
    current_task: str
    steps: list[dict]
    tools_used: list[str]
    output: str


class LangGraphAgent(BaseAgent):
    """LangGraph plugin with reasoning → tool_call → output flow."""

    def __init__(
        self,
        model_name: str = "gpt-4o",
        tools: list | None = None,
        system_prompt: str = "You are a helpful AI agent.",
        **_: Any,
    ) -> None:
        super().__init__()
        self.model_name = model_name
        self.tools = tools or []
        self.system_prompt = system_prompt

    async def execute(self, task: str) -> AgentResult:
        graph = self._build_graph()
        initial_state: AgentState = {
            "messages": [self.system_prompt],
            "current_task": task,
            "steps": [],
            "tools_used": [],
            "output": "",
        }

        try:
            final_state = await graph.ainvoke(initial_state)
        except Exception as exc:
            logger.exception("LangGraph agent execution failed: %s", exc)
            raise

        total_tokens = sum(len(s.get("content", "").split()) for s in final_state["steps"]) * 3
        pricing = MODEL_PRICING.get(self.model_name, {"input": 0.000001, "output": 0.000002})
        cost_usd = total_tokens * (pricing["input"] + pricing["output"]) / 2

        return AgentResult(
            output=final_state["output"],
            steps=final_state["steps"],
            tools_used=final_state["tools_used"],
            total_tokens=total_tokens,
            cost_usd=cost_usd,
        )

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("tool_call", self._tool_call_node)
        workflow.add_node("output", self._output_node)
        workflow.set_entry_point("reasoning")
        workflow.add_conditional_edges(
            "reasoning",
            self._should_use_tool,
            {"tool": "tool_call", "output": "output"},
        )
        workflow.add_edge("tool_call", "output")
        workflow.add_edge("output", END)
        return workflow.compile()

    async def _reasoning_node(self, state: AgentState) -> AgentState:
        await asyncio.sleep(0.1)
        content = (
            f"[{self.model_name}] Reasoning about task: {state['current_task'][:100]}. "
            f"Planning approach using {len(self.tools)} available tools."
        )
        duration_ms = 120
        step = {"step_type": "reasoning", "content": content, "duration_ms": duration_ms}
        state["steps"].append(step)
        state["messages"].append(content)
        if self.tracer:
            self.tracer.record_step(step_type="reasoning", content=content, duration_ms=duration_ms)
        return state

    async def _tool_call_node(self, state: AgentState) -> AgentState:
        await asyncio.sleep(0.08)
        tool_name = self.tools[0] if self.tools else "web_search"
        tool_input = {"query": state["current_task"][:80]}
        tool_output = {"status": "ok", "data": ["result_1", "result_2"]}
        content = f"Executing tool '{tool_name}' with model {self.model_name}"
        duration_ms = 90
        step = {
            "step_type": "tool_call",
            "content": content,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "duration_ms": duration_ms,
        }
        state["steps"].append(step)
        state["tools_used"].append(tool_name)
        if self.tracer:
            self.tracer.record_step(
                step_type="tool_call",
                content=content,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
                duration_ms=duration_ms,
            )
        return state

    async def _output_node(self, state: AgentState) -> AgentState:
        await asyncio.sleep(0.05)
        output = (
            f"[{self.model_name}] Completed: {state['current_task'][:120]}. "
            f"Used tools: {', '.join(state['tools_used']) or 'none'}."
        )
        duration_ms = 60
        step = {"step_type": "output", "content": output, "duration_ms": duration_ms}
        state["steps"].append(step)
        state["output"] = output
        if self.tracer:
            self.tracer.record_step(step_type="output", content=output, duration_ms=duration_ms)
        return state

    def _should_use_tool(self, state: AgentState) -> str:
        if self.tools or "search" in state["current_task"].lower():
            return "tool"
        return "output"
