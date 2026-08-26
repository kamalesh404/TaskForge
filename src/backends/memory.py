"""In-memory backend for testing and development."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from src.backends.base import Backend

logger = logging.getLogger("taskforge.backend.memory")


class MemoryBackend(Backend):
    """In-memory queue backend — not durable, useful for tests."""

    def __init__(self) -> None:
        self._queues: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.Lock()
        self._connected = False

    def connect(self) -> None:
        self._connected = True
        logger.info("Memory backend connected")

    def disconnect(self) -> None:
        self._connected = False
        self._queues.clear()
        logger.info("Memory backend disconnected")

    def push(self, queue_name: str, message: Dict[str, Any], priority: int = 0) -> None:
        with self._lock:
            msg = dict(message)
            msg["_priority"] = priority
            msg["_enqueued_at"] = time.time()
            self._queues[queue_name].append(msg)
            self._queues[queue_name].sort(
                key=lambda m: m.get("_priority", 0), reverse=True
            )
        logger.debug("Memory push to %s (priority=%d)", queue_name, priority)

    def pop(self, queue_name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            queue = self._queues.get(queue_name, [])
            if not queue:
                return None
            msg = queue.pop(0)
            msg.pop("_priority", None)
            msg.pop("_enqueued_at", None)
            return msg

    def peek(self, queue_name: str, count: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            queue = self._queues.get(queue_name, [])
            results = []
            for msg in queue[:count]:
                clean = dict(msg)
                clean.pop("_priority", None)
                clean.pop("_enqueued_at", None)
                results.append(clean)
            return results

    def length(self, queue_name: str) -> int:
        with self._lock:
            return len(self._queues.get(queue_name, []))

    def purge(self, queue_name: str) -> int:
        with self._lock:
            count = len(self._queues.get(queue_name, []))
            self._queues[queue_name] = []
            return count

    def ack(self, queue_name: str, message_id: str) -> bool:
        logger.debug("Memory ACK %s in %s", message_id, queue_name)
        return True

    def nack(self, queue_name: str, message_id: str) -> bool:
        logger.debug("Memory NACK %s in %s", message_id, queue_name)
        return True

    def is_connected(self) -> bool:
        return self._connected