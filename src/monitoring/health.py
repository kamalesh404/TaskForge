"""Worker health checks and heartbeat mechanism."""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("taskforge.health")


@dataclass
class WorkerStatus:
    """Snapshot of a worker's health status."""

    worker_id: str
    pid: int = field(default_factory=os.getpid)
    status: str = "unknown"  # healthy, unhealthy, unknown
    started_at: float = field(default_factory=time.time)
    last_heartbeat: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    current_task: Optional[str] = None
    uptime: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "pid": self.pid,
            "status": self.status,
            "started_at": self.started_at,
            "last_heartbeat": self.last_heartbeat,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "current_task": self.current_task,
            "uptime": time.time() - self.started_at,
        }


class HealthChecker:
    """Tracks worker health via periodic heartbeats."""

    _instances: Dict[str, HealthChecker] = {}

    def __init__(
        self,
        worker_id: str,
        heartbeat_interval: float = 30.0,
        timeout: float = 90.0,
    ) -> None:
        self.worker_id = worker_id
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timeout
        self._status = WorkerStatus(worker_id=worker_id)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        HealthChecker._instances[worker_id] = self

    def start_heartbeat(self) -> None:
        """Start the heartbeat thread."""
        self._running = True
        self._status.status = "healthy"
        self._status.last_heartbeat = time.time()
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()
        logger.info("Health checker started for %s", self.worker_id)

    def stop_heartbeat(self) -> None:
        """Stop the heartbeat thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._status.status = "stopped"
        logger.info("Health checker stopped for %s", self.worker_id)

    def record_task_dispatched(self, task_name: str) -> None:
        self._status.current_task = task_name

    def record_task_completed(self, result: Dict[str, Any]) -> None:
        self._status.current_task = None
        if result.get("status") == "success":
            self._status.tasks_completed += 1
        else:
            self._status.tasks_failed += 1

    def _heartbeat_loop(self) -> None:
        while self._running:
            self._status.last_heartbeat = time.time()
            logger.debug("Heartbeat from %s", self.worker_id)
            time.sleep(self.heartbeat_interval)

    @property
    def status(self) -> WorkerStatus:
        return self._status

    @classmethod
    def get_all_statuses(cls) -> List[Dict[str, Any]]:
        """Return status of all registered workers."""
        now = time.time()
        results = []
        for wid, checker in cls._instances.items():
            s = checker._status
            if now - s.last_heartbeat > checker.timeout and s.status == "healthy":
                s.status = "unhealthy"
            results.append(s.to_dict())
        return results