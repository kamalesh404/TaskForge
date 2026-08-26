"""Queue class with enqueue, dequeue, and priority support."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.backends.base import Backend


@dataclass
class QueueMessage:
    """A single message in the queue."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enqueued_at: float = field(default_factory=time.time)
    visible_at: float = 0.0
    attempts: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "task_name": self.task_name,
            "payload": self.payload,
            "priority": self.priority,
            "enqueued_at": self.enqueued_at,
            "visible_at": self.visible_at,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QueueMessage:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class Queue:
    """Task queue backed by a pluggable backend."""

    def __init__(
        self,
        name: str = "default",
        backend: Optional[Backend] = None,
    ) -> None:
        self.name = name
        self._backend = backend
        self._local_store: List[QueueMessage] = []

    def set_backend(self, backend: Backend) -> None:
        self._backend = backend

    def enqueue(
        self,
        task_name: str,
        payload: Dict[str, Any],
        priority: int = 0,
        delay_seconds: float = 0.0,
    ) -> str:
        """Add a task to the queue and return the message ID."""
        msg = QueueMessage(
            task_name=task_name,
            payload=payload,
            priority=priority,
            visible_at=time.time() + delay_seconds,
        )
        if self._backend:
            self._backend.push(self.name, msg.to_dict(), priority)
        else:
            self._local_store.append(msg)
            self._local_store.sort(key=lambda m: m.priority, reverse=True)
        return msg.message_id

    def dequeue(self, timeout: float = 1.0) -> Optional[QueueMessage]:
        """Pop the highest-priority visible message from the queue."""
        if self._backend:
            data = self._backend.pop(self.name)
            if data is None:
                return None
            msg = QueueMessage.from_dict(data)
            if msg.visible_at > time.time():
                self._backend.push(self.name, msg.to_dict(), msg.priority)
                return None
            return msg

        now = time.time()
        for idx, msg in enumerate(self._local_store):
            if msg.visible_at <= now:
                self._local_store.pop(idx)
                msg.attempts += 1
                return msg
        return None

    def peek(self, count: int = 10) -> List[QueueMessage]:
        """Return messages without removing them."""
        if self._backend:
            items = self._backend.peek(self.name, count)
            return [QueueMessage.from_dict(d) for d in items]
        return self._local_store[:count]

    def size(self) -> int:
        if self._backend:
            return self._backend.length(self.name)
        return len(self._local_store)

    def purge(self) -> int:
        """Remove all messages. Returns count removed."""
        if self._backend:
            return self._backend.purge(self.name)
        count = len(self._local_store)
        self._local_store.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        return {
            "queue_name": self.name,
            "depth": self.size(),
            "backend": type(self._backend).__name__ if self._backend else "local",
        }