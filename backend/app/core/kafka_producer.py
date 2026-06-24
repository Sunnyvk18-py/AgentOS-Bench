import json
import logging
from datetime import datetime, timezone

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KafkaEvalProducer:
    """Streams evaluation events to Kafka with graceful degradation."""

    def __init__(self) -> None:
        self._producer = None
        self._available = False
        self._initialize()

    def _initialize(self) -> None:
        try:
            from confluent_kafka import Producer

            self._producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
            self._available = True
            logger.info("Kafka producer connected to %s", settings.KAFKA_BOOTSTRAP_SERVERS)
        except Exception as exc:
            logger.warning("Kafka producer unavailable, continuing without streaming: %s", exc)
            self._available = False

    async def produce_event(self, topic: str, event_type: str, payload: dict) -> None:
        if not self._available or self._producer is None:
            logger.debug("Kafka unavailable, skipping event %s", event_type)
            return

        message = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload,
        }

        try:
            serialized = json.dumps(message).encode("utf-8")
            self._producer.produce(topic, serialized)
            self._producer.poll(0)
            logger.debug("Produced Kafka event %s to %s", event_type, topic)
        except Exception as exc:
            logger.warning("Failed to produce Kafka event: %s", exc)

    def flush(self) -> None:
        if self._producer is not None:
            try:
                self._producer.flush(timeout=1.0)
            except Exception as exc:
                logger.warning("Kafka flush failed: %s", exc)


kafka_producer = KafkaEvalProducer()
