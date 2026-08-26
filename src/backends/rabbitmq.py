"""RabbitMQ backend with exchanges, bindings, and message acknowledgment."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from src.backends.base import Backend

logger = logging.getLogger("taskforge.backend.rabbitmq")


class RabbitMQBackend(Backend):
    """Queue backend backed by RabbitMQ via AMQP."""

    def __init__(
        self,
        url: str = "amqp://guest:guest@localhost:5672/",
        exchange: str = "taskforge",
    ) -> None:
        self.url = url
        self.exchange_name = exchange
        self._connection: Any = None
        self._channel: Any = None

    def connect(self) -> None:
        try:
            import pika
            params = pika.URLParameters(self.url)
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            self._channel.exchange_declare(
                exchange=self.exchange_name, exchange_type="direct", durable=True
            )
            logger.info("Connected to RabbitMQ at %s", self.url)
        except ImportError:
            raise ImportError("Install 'pika' package: pip install pika>=1.3")
        except Exception as exc:
            raise ConnectionError(f"Failed to connect to RabbitMQ: {exc}") from exc

    def disconnect(self) -> None:
        if self._connection and self._connection.is_open:
            self._connection.close()
            logger.info("Disconnected from RabbitMQ")

    def _ensure_queue(self, queue_name: str) -> None:
        """Declare a durable queue bound to the exchange."""
        self._channel.queue_declare(queue=queue_name, durable=True)
        self._channel.queue_bind(
            queue=queue_name, exchange=self.exchange_name, routing_key=queue_name
        )

    def push(self, queue_name: str, message: Dict[str, Any], priority: int = 0) -> None:
        self._ensure_queue(queue_name)
        body = json.dumps(message)
        props = {"priority": priority, "delivery_mode": 2}
        self._channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=queue_name,
            body=body,
            properties=pika.BasicProperties(**props),
        )
        logger.debug("Published to %s (priority=%d)", queue_name, priority)

    def pop(self, queue_name: str) -> Optional[Dict[str, Any]]:
        self._ensure_queue_queue(queue_name)
        method, _props, body = self._channel.basic_get(queue=queue_name, auto_ack=False)
        if method is None:
            return None
        self._channel.basic_ack(delivery_tag=method.delivery_tag)
        return json.loads(body)

    def _ensure_queue_queue(self, queue_name: str) -> None:
        """Declare queue without binding for get operations."""
        self._channel.queue_declare(queue=queue_name, durable=True)

    def peek(self, queue_name: str, count: int = 10) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []
        for _ in range(count):
            method, _props, body = self._channel.basic_get(queue=queue_name, auto_ack=False)
            if method is None:
                break
            messages.append(json.loads(body))
            self._channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        return messages

    def length(self, queue_name: str) -> int:
        self._ensure_queue(queue_name)
        queue = self._channel.queue_declare(queue=queue_name, passive=True)
        return queue.method.message_count

    def purge(self, queue_name: str) -> int:
        self._ensure_queue(queue_name)
        result = self._channel.queue_purge(queue=queue_name)
        return result.method.message_count

    def ack(self, queue_name: str, message_id: str) -> bool:
        logger.debug("ACK for %s in %s", message_id, queue_name)
        return True

    def nack(self, queue_name: str, message_id: str) -> bool:
        logger.warning("NACK for %s in %s", message_id, queue_name)
        return True