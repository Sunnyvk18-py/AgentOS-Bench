"""
AgentOS Bench — Agent Plugin Template
======================================
Copy this file to backend/app/agents/your_agent_name.py
The server will auto-discover it. No restarts needed.

Or use the CLI:
    agentbench agents add ./your_agent_name.py
"""

from app.agents.base import AgentResult, BaseAgent


class YourAgentName(BaseAgent):
    # ── Required metadata ──────────────────────────────────────────────
    # These are auto-read by the discovery engine.
    __agent_name__ = "your_agent"           # Must be unique, lowercase, no spaces
    __agent_description__ = "Describe what this agent does in one sentence."
    __agent_config_schema__ = {
        # Optional: declare config parameters your agent accepts.
        # These show up in the UI's New Eval Run form.
        "temperature": {"type": "float", "default": 0.7},
        "model_name": {"type": "str", "default": "gpt-4o"},
    }

    # ── Constructor ────────────────────────────────────────────────────
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.7, **kwargs):
        super().__init__()
        self.model_name = model_name
        self.temperature = temperature

    # ── Main method (required) ─────────────────────────────────────────
    async def execute(self, task: str) -> AgentResult:
        """
        Run your agent logic here.
        self.tracer is auto-injected by EvalRunner — call record_step()
        at each meaningful point so the trace timeline populates.
        """

        # Step 1 — Record a reasoning step
        if self.tracer:
            self.tracer.record_step(
                step_type="reasoning",          # reasoning | tool_call | memory_read | output
                content=f"Planning approach for: {task[:120]}",
                duration_ms=100,                # approximate ms this step took
            )

        # ── Your real agent logic goes here ───────────────────────────
        # Examples:
        #   output = await my_langgraph_graph.ainvoke({"task": task})
        #   output = await my_openai_client.chat(task)
        #   output = await my_crewai_crew.kickoff(task)
        output = f"Completed: {task}"

        # Step 2 — Record a tool call step (if your agent uses tools)
        if self.tracer:
            self.tracer.record_step(
                step_type="tool_call",
                content="Queried internal knowledge base",
                tool_name="search_kb",          # must match tools_used below for precision scoring
                tool_input={"query": task},
                tool_output={"results": ["result1", "result2"]},
                duration_ms=250,
            )

        # Step 3 — Record the final output step
        if self.tracer:
            self.tracer.record_step(
                step_type="output",
                content=output,
                duration_ms=50,
            )

        return AgentResult(
            output=output,
            tools_used=["search_kb"],   # list of tool names actually used (for precision scoring)
            total_tokens=350,           # total tokens consumed (affects cost metric)
            cost_usd=0.0012,            # actual cost in USD (affects cost metric)
        )
