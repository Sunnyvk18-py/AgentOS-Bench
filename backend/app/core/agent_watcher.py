import logging
import threading
from pathlib import Path
from typing import Callable

from app.core.agent_discovery import AGENTS_DIR, SKIP_FILES

logger = logging.getLogger(__name__)


class AgentWatcher:
    """Polls the agents directory and triggers reload on changes (daemon thread)."""

    def __init__(self, on_change: Callable[[], None], interval: float = 2.0) -> None:
        self._on_change = on_change
        self._interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._snapshot: dict[str, float] = {}

    def _current_snapshot(self) -> dict[str, float]:
        snapshot: dict[str, float] = {}
        for path in AGENTS_DIR.glob("*.py"):
            if path.name in SKIP_FILES:
                continue
            try:
                snapshot[path.name] = path.stat().st_mtime
            except OSError:
                continue
        return snapshot

    def _run(self) -> None:
        self._snapshot = self._current_snapshot()
        while not self._stop.is_set():
            try:
                current = self._current_snapshot()
                if current != self._snapshot:
                    logger.info("Agent directory change detected, reloading registry")
                    self._snapshot = current
                    self._on_change()
            except Exception as exc:
                logger.warning("AgentWatcher error: %s", exc)
            self._stop.wait(self._interval)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="AgentWatcher", daemon=True)
        self._thread.start()
        logger.info("AgentWatcher started on %s", AGENTS_DIR)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("AgentWatcher stopped")
