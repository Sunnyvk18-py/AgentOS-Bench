import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AgentEventBus:
    """Broadcasts agent registry events to SSE subscribers."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    def publish_sync(self, event_type: str, payload: dict[str, Any]) -> None:
        message = {"event": event_type, "payload": payload}
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(message)
            except Exception as exc:
                logger.debug("Failed to enqueue agent event: %s", exc)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        self.publish_sync(event_type, payload)


agent_event_bus = AgentEventBus()


def format_sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event)}\n\n"
