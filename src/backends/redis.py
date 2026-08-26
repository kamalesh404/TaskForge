"""Redis backend using pub/sub and sorted sets for priority queues."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from src.backends.base import Backend

logger = logging.getLogger("taskforge.backend.redis")


class RedisBackend(Backend):
    """Queue backend backed by Redis sorted sets and pub/sub."""

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        self.url = url
        self._client: Any = None
        self._pubsub: Any = None

    def connect(self) -> None:
        try:
            import redis as redis_lib
            self._client = redis_lib.Redis.from_url(
                self.url, decode_responses=True, socket_timeout=10
            )
            self._client.ping()
            logger.info("Connected to Redis at %s", self.url)
        except ImportError:
            raise ImportError("Install 'redis' package: pip install redis>=4.0")
        except Exception as exc:
            raise ConnectionError(f"Failed to connect to Redis: {exc}") from exc

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            logger.info("Disconnected from Redis")

    def push(self, queue_name: str, message: Dict[str, Any], priority: int = 0) -> None:
        key = f"taskforge:queue:{queue_name}"
        self._client.zadd(key, {json.dumps(message): priority})
        self._client.publish(f"taskforge:notify:{queue_name}", "new_task")
        logger.debug("Pushed message to %s (priority=%d)", queue_name, priority)

    def pop(self, queue_name: str) -> Optional[Dict[str, Any]]:
        key = f"taskforge:queue:{queue_name}"
        items = self._client.zpopmin(key, count=1)
        if not items:
            return None
        raw, _score = items[0]
        return json.loads(raw)

    def peek(self, queue_name: str, count: int = 10) -> List[Dict[str, Any]]:
        key = f"taskforge:queue:{queue_name}"
        items = self._client.zrange(key, 0, count - 1, withscores=True)
        return [json.loads(raw) for raw, _score in items]

    def length(self, queue_name: str) -> int:
        key = f"taskforge:queue:{queue_name}"
        return self._client.zcard(key)

    def purge(self, queue_name: str) -> int:
        key = f"taskforge:queue:{queue_name}"
        count = self._client.zcard(key)
        self._client.delete(key)
        return count

    def ack(self, queue_name: str, message_id: str) -> bool:
        ack_key = f"taskforge:ack:{queue_name}"
        self._client.sadd(ack_key, message_id)
        return True

    def nack(self, queue_name: str, message_id: str) -> bool:
        logger.warning("NACK received for message %s in queue %s", message_id, queue_name)
        return True

    def subscribe(self, queue_name: str, callback: Any) -> None:
        """Subscribe to task notifications on a queue."""
        self._pubsub = self._client.pubsub()
        self._pubsub.subscribe(**{f"taskforge:notify:{queue_name}": callback})

    def is_connected(self) -> bool:
        try:
            return self._client is not None and self._client.ping()
        except Exception:
            return False