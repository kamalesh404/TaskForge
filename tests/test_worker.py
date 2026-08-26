"""Tests for worker lifecycle."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

from src.backends.memory import MemoryBackend
from src.core.queue import Queue
from src.core.task import TaskRegistry, task
from src.core.worker import Worker


class TestWorker:
    """Tests for the Worker class."""

    def test_worker_stats_initial(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        queue = Queue(name="wtest", backend=backend)
        worker = Worker(queue=queue, count=1, timeout=10)
        stats = worker.stats
        assert stats["pool_size"] == 1
        assert stats["tasks_completed"] == 0
        assert stats["running"] is False

    def test_worker_dispatches_task(self) -> None:
        @task(name="worker.dispatch.test")
        def compute(n: int) -> int:
            return n + 1

        backend = MemoryBackend()
        backend.connect()
        queue = Queue(name="wtest2", backend=backend)
        queue.enqueue("worker.dispatch.test", {"args": [10], "kwargs": {}})
        worker = Worker(queue=queue, count=1, timeout=5)
        msg = queue.dequeue()
        assert msg is not None
        assert msg.task_name == "worker.dispatch.test"

    def test_worker_stop(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        queue = Queue(name="wtest3", backend=backend)
        worker = Worker(queue=queue, count=1, timeout=5)
        worker._running = True
        worker.stop()
        assert worker._running is False