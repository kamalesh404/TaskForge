"""Task execution metrics: timing, success/failure rates."""

from __future__ import annotations

import statistics
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TaskMetric:
    """A single task execution metric record."""

    task_name: str
    status: str  # "success" or "failure"
    elapsed: float
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None
    worker_id: str = ""


class MetricsCollector:
    """Thread-safe collector for task execution metrics."""

    _instance: Optional[MetricsCollector] = None

    def __new__(cls) -> MetricsCollector:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._metrics: List[TaskMetric] = []
            cls._instance._lock = threading.Lock()
            cls._instance._counters: Dict[str, int] = defaultdict(int)
        return cls._instance

    def record(
        self,
        task_name: str,
        status: str,
        elapsed: float,
        error: Optional[str] = None,
        worker_id: str = "",
    ) -> None:
        metric = TaskMetric(
            task_name=task_name,
            status=status,
            elapsed=elapsed,
            error=error,
            worker_id=worker_id,
        )
        with self._lock:
            self._metrics.append(metric)
            self._counters[f"{task_name}:{status}"] += 1
            self._counters["total"] += 1
            self._counters[f"total:{status}"] += 1

    def get_task_stats(self, task_name: str) -> Dict[str, Any]:
        with self._lock:
            task_metrics = [m for m in self._metrics if m.task_name == task_name]
        if not task_metrics:
            return {"task_name": task_name, "count": 0}
        successes = [m for m in task_metrics if m.status == "success"]
        failures = [m for m in task_metrics if m.status == "failure"]
        elapsed_values = [m.elapsed for m in task_metrics]
        return {
            "task_name": task_name,
            "count": len(task_metrics),
            "successes": len(successes),
            "failures": len(failures),
            "success_rate": len(successes) / len(task_metrics) * 100,
            "avg_elapsed": statistics.mean(elapsed_values),
            "p50_elapsed": statistics.median(elapsed_values),
            "p99_elapsed": sorted(elapsed_values)[int(len(elapsed_values) * 0.99)]
            if len(elapsed_values) > 1
            else elapsed_values[0],
            "max_elapsed": max(elapsed_values),
            "min_elapsed": min(elapsed_values),
        }

    def get_overview(self) -> Dict[str, Any]:
        with self._lock:
            counters = dict(self._counters)
        return {
            "total_tasks": counters.get("total", 0),
            "total_success": counters.get("total:success", 0),
            "total_failure": counters.get("total:failure", 0),
            "counters": counters,
        }

    def get_recent(self, count: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            recent = self._metrics[-count:]
        return [
            {
                "task_name": m.task_name,
                "status": m.status,
                "elapsed": m.elapsed,
                "timestamp": m.timestamp,
                "error": m.error,
            }
            for m in recent
        ]

    def reset(self) -> None:
        with self._lock:
            self._metrics.clear()
            self._counters.clear()