import asyncio
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.run import AgentStep

logger = logging.getLogger(__name__)
settings = get_settings()


class KafkaEvalConsumer:
    """Background consumer that persists eval step events to the database."""

    def __init__(self) -> None:
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("Kafka consumer background task started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Kafka consumer stopped")

    async def _consume_loop(self) -> None:
        while self._running:
            try:
                await self._consume_once()
            except Exception as exc:
                logger.warning("Kafka consumer error, retrying in 5s: %s", exc)
                await asyncio.sleep(5)

    async def _consume_once(self) -> None:
        try:
            from confluent_kafka import Consumer, KafkaError
        except ImportError:
            logger.warning("confluent_kafka not available for consumer")
            await asyncio.sleep(30)
            return

        consumer = None
        try:
            consumer = Consumer(
                {
                    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                    "group.id": "agentos-bench-consumer",
                    "auto.offset.reset": "earliest",
                    "enable.auto.commit": True,
                }
            )
            consumer.subscribe([settings.KAFKA_TOPIC_EVAL_EVENTS])

            while self._running:
                msg = await asyncio.to_thread(consumer.poll, 1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.warning("Kafka consumer error: %s", msg.error())
                    continue
                await self._handle_message(msg.value())
        except Exception as exc:
            logger.warning("Kafka consumer connection failed: %s", exc)
            await asyncio.sleep(10)
        finally:
            if consumer is not None:
                consumer.close()

    async def _handle_message(self, raw: bytes) -> None:
        try:
            data = json.loads(raw.decode("utf-8"))
            payload = data.get("payload", {})
            event_type = data.get("event_type", "")

            if event_type != "agent_step":
                return

            run_id = payload.get("run_id")
            step_data = payload.get("step")
            if not run_id or not step_data:
                return

            async with AsyncSessionLocal() as session:
                existing = await session.execute(
                    select(AgentStep).where(
                        AgentStep.run_id == run_id,
                        AgentStep.step_index == step_data.get("step_index"),
                    )
                )
                if existing.scalar_one_or_none():
                    return

                step = AgentStep(
                    id=step_data.get("id", str(uuid.uuid4())),
                    run_id=run_id,
                    step_index=step_data["step_index"],
                    step_type=step_data["step_type"],
                    content=step_data["content"],
                    tool_name=step_data.get("tool_name"),
                    tool_input=step_data.get("tool_input"),
                    tool_output=step_data.get("tool_output"),
                    duration_ms=step_data.get("duration_ms", 0),
                    timestamp=datetime.fromisoformat(step_data["timestamp"])
                    if step_data.get("timestamp")
                    else datetime.utcnow(),
                )
                session.add(step)
                await session.commit()
        except json.JSONDecodeError as exc:
            logger.error("Dead-letter: invalid JSON in Kafka message: %s", exc)
        except Exception as exc:
            logger.error("Dead-letter: failed to persist Kafka message: %s", exc)


kafka_consumer = KafkaEvalConsumer()
