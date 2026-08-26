"""Backend base class for Redis, RabbitMQ, and SQLite storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Backend(ABC):
    """Abstract interface that all queue backends must implement."""

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the backing store."""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the backing store."""
        ...

    @abstractmethod
    def push(self, queue_name: str, message: Dict[str, Any], priority: int = 0) -> None:
        """Push a message onto the named queue."""
        ...

    @abstractmethod
    def pop(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Pop the highest-priority message from the named queue."""
        ...

    @abstractmethod
    def peek(self, queue_name: str, count: int = 10) -> List[Dict[str, Any]]:
        """Return up to *count* messages without removing them."""
        ...

    @abstractmethod
    def length(self, queue_name: str) -> int:
        """Return the current depth of the named queue."""
        ...

    @abstractmethod
    def purge(self, queue_name: str) -> int:
        """Remove all messages from the named queue. Returns count removed."""
        ...

    @abstractmethod
    def ack(self, queue_name: str, message_id: str) -> bool:
        """Acknowledge successful processing of a message."""
        ...

    @abstractmethod
    def nack(self, queue_name: str, message_id: str) -> bool:
        """Negative-acknowledge a message so it can be retried."""
        ...

    def is_connected(self) -> bool:
        """Check if the backend connection is alive."""
        return True