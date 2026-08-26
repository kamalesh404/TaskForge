"""Tests for queue operations."""

from __future__ import annotations

from src.core.queue import Queue, QueueMessage


class TestQueueMessage:
    """Tests for QueueMessage data class."""

    def test_to_dict_roundtrip(self) -> None:
        msg = QueueMessage(task_name="test", payload={"key": "value"})
        data = msg.to_dict()
        restored = QueueMessage.from_dict(data)
        assert restored.task_name == "test"
        assert restored.payload == {"key": "value"}
        assert restored.message_id == msg.message_id


class TestQueue:
    """Tests for the Queue class."""

    def test_enqueue_and_dequeue(self, queue: Queue) -> None:
        queue.enqueue("task.a", {"x": 1})
        msg = queue.dequeue()
        assert msg is not None
        assert msg.task_name == "task.a"

    def test_empty_dequeue(self, queue: Queue) -> None:
        assert queue.dequeue() is None

    def test_priority_order(self, queue: Queue) -> None:
        queue.enqueue("low", {}, priority=1)
        queue.enqueue("high", {}, priority=10)
        queue.enqueue("mid", {}, priority=5)
        first = queue.dequeue()
        assert first is not None
        assert first.task_name == "high"

    def test_peek_does_not_remove(self, queue: Queue) -> None:
        queue.enqueue("peek.test", {"v": 1})
        peeked = queue.peek(count=1)
        assert len(peeked) == 1
        assert queue.size() == 1

    def test_purge(self, queue: Queue) -> None:
        queue.enqueue("a", {})
        queue.enqueue("b", {})
        count = queue.purge()
        assert count == 2
        assert queue.size() == 0

    def test_stats(self, queue: Queue) -> None:
        queue.enqueue("x", {})
        stats = queue.stats()
        assert stats["depth"] == 1
        assert stats["queue_name"] == "test_queue"

    def test_local_size(self, queue: Queue) -> None:
        assert queue.size() == 0
        queue.enqueue("a", {})
        assert queue.size() == 1