"""Dashboard API routes for tasks, workers, queues, and metrics."""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from fastapi import APIRouter
except ImportError:
    APIRouter = None  # type: ignore[assignment,misc]

from src.dashboard.models import (
    MetricsResponse,
    QueueStatsResponse,
    TaskListResponse,
    WorkerStatusResponse,
)

if APIRouter is not None:
    router = APIRouter()
else:
    router = None  # type: ignore[assignment]

if APIRouter is not None:
    @router.get("/metrics", response_model=MetricsResponse)
    async def get_metrics() -> MetricsResponse:
        """Return overall task execution metrics."""
        from src.monitoring.metrics import MetricsCollector
        collector = MetricsCollector()
        overview = collector.get_overview()
        return MetricsResponse(
            total_tasks=overview["total_tasks"],
            total_success=overview["total_success"],
            total_failure=overview["total_failure"],
            counters=overview["counters"],
        )

    @router.get("/workers", response_model=List[WorkerStatusResponse])
    async def get_workers() -> List[WorkerStatusResponse]:
        """Return status of all active workers."""
        from src.monitoring.health import HealthChecker
        statuses = HealthChecker.get_all_statuses()
        return [WorkerStatusResponse(**s) for s in statuses]

    @router.get("/queues/{queue_name}", response_model=QueueStatsResponse)
    async def get_queue_stats(queue_name: str) -> QueueStatsResponse:
        """Return statistics for a specific queue."""
        from src.core.queue import Queue
        q = Queue(name=queue_name)
        stats = q.stats()
        return QueueStatsResponse(**stats)

    @router.get("/tasks", response_model=TaskListResponse)
    async def list_tasks() -> TaskListResponse:
        """List all registered tasks."""
        from src.core.task import TaskRegistry
        registry = TaskRegistry()
        tasks = [t.to_dict() for t in registry.list_tasks()]
        return TaskListResponse(tasks=tasks, count=len(tasks))

    @router.get("/tasks/recent")
    async def get_recent_tasks(count: int = 50) -> Dict[str, Any]:
        """Return recent task execution history."""
        from src.monitoring.metrics import MetricsCollector
        collector = MetricsCollector()
        return {"recent": collector.get_recent(count)}

    @router.get("/health")
    async def health_check() -> Dict[str, str]:
        return {"status": "healthy"}