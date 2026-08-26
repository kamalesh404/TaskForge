"""Event emitter for task lifecycle events."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("taskforge.events")


class EventEmitter:
    """Publish-subscribe event emitter for task lifecycle hooks."""

    _instance: Optional[EventEmitter] = None

    def __new__(cls) -> EventEmitter:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners: Dict[str, List[Callable]] = defaultdict(list)
            cls._instance._lock = threading.Lock()
            cls._instance._history: List[Dict[str, Any]] = []
        return cls._instance

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for a named event."""
        with self._lock:
            self._listeners[event].append(callback)
        logger.debug("Registered listener for '%s'", event)

    def off(self, event: str, callback: Callable) -> None:
        """Remove a specific callback from an event."""
        with self._lock:
            listeners = self._listeners.get(event, [])
            self._listeners[event] = [cb for cb in listeners if cb is not callback]

    def emit(self, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event to all registered listeners."""
        event_data = {
            "event": event,
            "data": data or {},
            "timestamp": time.time(),
        }
        with self._lock:
            self._history.append(event_data)
            listeners = list(self._listeners.get(event, []))
            wildcard_listeners = list(self._listeners.get("*", []))

        all_listeners = listeners + wildcard_listeners
        for callback in all_listeners:
            try:
                callback(event_data)
            except Exception as exc:
                logger.error("Error in listener for '%s': %s", event, exc)

    def get_history(self, event: Optional[str] = None, count: int = 50) -> List[Dict[str, Any]]:
        """Return recent event history, optionally filtered by event name."""
        with self._lock:
            history = self._history
        if event:
            history = [e for e in history if e["event"] == event]
        return history[-count:]

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()

    def listener_count(self, event: str) -> int:
        with self._lock:
            return len(self._listeners.get(event, []))


def wildcard_listener(
    listeners: List[Callable], event_data: Dict[str, Any]
) -> List[Any]:
    """Invoke wildcard listeners that receive all events."""
    for callback in listeners:
        try:
            callback(event_data)
        except Exception as exc:
            logger.error("Wildcard listener error: %s", exc)
    return []


# Standard lifecycle events
EVENT_TASK_QUEUED = "task.queued"
EVENT_TASK_STARTED = "task.started"
EVENT_TASK_COMPLETED = "task.completed"
EVENT_TASK_FAILED = "task.failed"
EVENT_TASK_RETRYING = "task.retrying"
EVENT_WORKER_STARTED = "worker.started"
EVENT_WORKER_STOPPED = "worker.stopped"
EVENT_WORKER_HEARTBEAT = "worker.heartbeat"