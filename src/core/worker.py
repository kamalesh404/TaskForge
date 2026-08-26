"""Worker class with process pool and graceful shutdown."""

from __future__ import annotations

import logging
import multiprocessing
import os
import signal
import time
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Any, Dict, List, Optional

from src.core.queue import Queue, QueueMessage
from src.core.task import TaskRegistry
from src.monitoring.health import HealthChecker

logger = logging.getLogger("taskforge.worker")


def _execute_task(
    task_name: str,
    payload: Dict[str, Any],
    backend_url: str,
) -> Dict[str, Any]:
    """Run a single task in a worker process."""
    registry = TaskRegistry()
    metadata = registry.get(task_name)
    args = payload.get("args", ())
    kwargs = payload.get("kwargs", {})
    start = time.monotonic()
    try:
        result = metadata.func(*args, **kwargs)
        elapsed = time.monotonic() - start
        return {"status": "success", "result": result, "elapsed": elapsed}
    except Exception as exc:
        elapsed = time.monotonic() - start
        logger.error("Task %s failed: %s", task_name, exc)
        return {"status": "failure", "error": str(exc), "elapsed": elapsed}


class Worker:
    """Manages a pool of worker processes that consume tasks from a queue."""

    def __init__(
        self,
        queue: Queue,
        count: int = 4,
        timeout: int = 300,
        backend_url: str = "",
    ) -> None:
        self.queue = queue
        self.count = count or multiprocessing.cpu_count()
        self.timeout = timeout
        self.backend_url = backend_url
        self._running = False
        self._executor: Optional[ProcessPoolExecutor] = None
        self._futures: Dict[str, Future] = {}
        self._health = HealthChecker(worker_id=f"worker-{os.getpid()}")
        self._tasks_completed = 0
        self._tasks_failed = 0

    def start(self) -> None:
        """Start consuming tasks from the queue."""
        self._running = True
        self._executor = ProcessPoolExecutor(max_workers=self.count)
        logger.info("Worker pool started with %d processes", self.count)
        self._health.start_heartbeat()
        self._consume_loop()

    def stop(self, signum: Optional[int] = None, frame: Any = None) -> None:
        """Gracefully shut down the worker pool."""
        logger.info("Worker shutting down (signal=%s)", signum)
        self._running = False
        self._health.stop_heartbeat()
        if self._executor:
            self._executor.shutdown(wait=True, cancel_futures=False)
        logger.info(
            "Worker stopped — completed: %d, failed: %d",
            self._tasks_completed,
            self._tasks_failed,
        )

    def _consume_loop(self) -> None:
        """Main loop that dequeues and dispatches tasks."""
        while self._running:
            msg = self.queue.dequeue(timeout=1.0)
            if msg is None:
                time.sleep(0.1)
                continue
            self._dispatch(msg)
            self._collect_finished()

    def _dispatch(self, msg: QueueMessage) -> None:
        """Submit a task to the process pool."""
        if self._executor is None:
            return
        future = self._executor.submit(
            _execute_task,
            msg.task_name,
            msg.payload,
            self.backend_url,
        )
        self._futures[msg.message_id] = future
        self._health.record_task_dispatched(msg.task_name)
        logger.info("Dispatched task %s (id=%s)", msg.task_name, msg.message_id)

    def _collect_finished(self) -> None:
        """Check completed futures and update counters."""
        finished = [k for k, f in self._futures.items() if f.done()]
        for msg_id in finished:
            future = self._futures.pop(msg_id)
            result = future.result(timeout=1)
            if result["status"] == "success":
                self._tasks_completed += 1
            else:
                self._tasks_failed += 1
            self._health.record_task_completed(result)

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "pid": os.getpid(),
            "pool_size": self.count,
            "running": self._running,
            "tasks_completed": self._tasks_completed,
            "tasks_failed": self._tasks_failed,
            "pending_futures": len(self._futures),
        }

    def register_signals(self) -> None:
        """Register signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)