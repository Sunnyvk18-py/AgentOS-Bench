import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(255), nullable=False)
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hallucination_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tool_call_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    steps: Mapped[list["AgentStep"]] = relationship(
        "AgentStep", back_populates="run", cascade="all, delete-orphan"
    )


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("eval_runs.id", ondelete="CASCADE"), nullable=False
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_input: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tool_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    run: Mapped["EvalRun"] = relationship("EvalRun", back_populates="steps")


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    benchmark_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    models_compared: Mapped[list] = mapped_column(JSON, nullable=False)
    results: Mapped[dict] = mapped_column(JSON, nullable=False)
    winner_model: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
