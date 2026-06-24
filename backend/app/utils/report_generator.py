from datetime import datetime
from typing import Any

from app.models.run import AgentStep, EvalRun


class ReportGenerator:
    """Generates JSON and Markdown evaluation reports."""

    @staticmethod
    def _score_emoji(score: float | None) -> str:
        if score is None:
            return "➖"
        if score > 0.8:
            return "✅"
        if score >= 0.5:
            return "⚠️"
        return "❌"

    def generate_json_report(self, run: EvalRun, steps: list[AgentStep]) -> dict[str, Any]:
        return {
            "run_id": run.id,
            "agent_name": run.agent_name,
            "llm_model": run.llm_model,
            "task_description": run.task_description,
            "status": run.status,
            "scores": {
                "composite": run.composite_score,
                "accuracy": run.accuracy_score,
                "hallucination": run.hallucination_score,
                "tool_call_precision": run.tool_call_precision,
            },
            "performance": {
                "latency_ms": run.latency_ms,
                "cost_usd": run.cost_usd,
                "total_steps": run.total_steps,
            },
            "timestamps": {
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            },
            "insights": self._generate_insights(run),
            "steps": [
                {
                    "step_index": s.step_index,
                    "step_type": s.step_type,
                    "content": s.content,
                    "tool_name": s.tool_name,
                    "tool_input": s.tool_input,
                    "tool_output": s.tool_output,
                    "duration_ms": s.duration_ms,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                }
                for s in steps
            ],
        }

    def generate_markdown_report(self, run: EvalRun, steps: list[AgentStep]) -> str:
        lines = [
            f"# Eval Run Report: `{run.id[:8]}`",
            "",
            "## Run Metadata",
            "",
            "| Field | Value |",
            "|-------|-------|",
            f"| Agent | {run.agent_name} |",
            f"| Model | {run.llm_model} |",
            f"| Status | {run.status} |",
            f"| Created | {run.created_at} |",
            f"| Completed | {run.completed_at or 'N/A'} |",
            "",
            "## Score Breakdown",
            "",
            f"| Metric | Score | Indicator |",
            f"|--------|-------|-----------|",
            f"| Composite | {run.composite_score} | {self._score_emoji(run.composite_score)} |",
            f"| Accuracy | {run.accuracy_score} | {self._score_emoji(run.accuracy_score)} |",
            f"| Hallucination (raw) | {run.hallucination_score} | {self._score_emoji(1 - (run.hallucination_score or 0))} |",
            f"| Tool Precision | {run.tool_call_precision} | {self._score_emoji(run.tool_call_precision)} |",
            f"| Latency | {run.latency_ms} ms | — |",
            f"| Cost | ${run.cost_usd:.6f} | — |",
            "",
            "## Insights",
            "",
        ]
        for insight in self._generate_insights(run):
            lines.append(f"- {insight}")

        lines.extend(["", "## Step-by-Step Trace", ""])
        for step in steps:
            lines.extend(
                [
                    f"<details>",
                    f"<summary>Step {step.step_index + 1}: {step.step_type} ({step.duration_ms}ms)</summary>",
                    "",
                    step.content,
                    "",
                ]
            )
            if step.tool_name:
                lines.append(f"**Tool:** `{step.tool_name}`")
                lines.append(f"**Input:** `{step.tool_input}`")
                lines.append(f"**Output:** `{step.tool_output}`")
            lines.extend(["", "</details>", ""])

        return "\n".join(lines)

    @staticmethod
    def _generate_insights(run: EvalRun) -> list[str]:
        insights: list[str] = []
        if run.composite_score is not None:
            if run.composite_score > 0.8:
                insights.append("Strong overall performance across all metrics.")
            elif run.composite_score < 0.5:
                insights.append("Below threshold — review agent configuration and prompts.")
        if run.hallucination_score is not None and run.hallucination_score > 0.5:
            insights.append("High hallucination detected — consider adding grounding context.")
        if run.latency_ms is not None and run.latency_ms > 5000:
            insights.append("Latency exceeds 5s — optimize tool calls or model selection.")
        if run.cost_usd is not None and run.cost_usd > 0.05:
            insights.append("Cost is elevated — review token usage and model pricing.")
        if not insights:
            insights.append("Run completed within expected parameters.")
        return insights
