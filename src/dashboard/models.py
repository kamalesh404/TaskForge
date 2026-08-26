"""Pydantic response models for the dashboard API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel
except ImportError:
    # Minimal fallback when pydantic is not installed
    class BaseModel:  # type: ignore[no-redef]
        pass


class MetricsResponse(BaseModel):
    """Response model for /api/metrics endpoint."""

    total_tasks: int = 0
    total_success: int = 0
    total_failure: int = 0
    counters: Dict[str, int] = {}


class WorkerStatusResponse(BaseModel):
    """Response model for /api/workers endpoint."""

    worker_id: str = ""
    pid: int = 0
    status: str = "unknown"
    started_at: float = 0.0
    last_heartbeat: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    current_task: Optional[str] = None
    uptime: float = 0.0


class QueueStatsResponse(BaseModel):
    """Response model for /api/queues/{name} endpoint."""

    queue_name: str = ""
    depth: int = 0
    backend: str = "unknown"


class TaskMetadataResponse(BaseModel):
    """Response model for a single registered task."""

    name: str = ""
    queue: str = "default"
    priority: int = 0
    retries: int = 0
    timeout: Optional[int] = None
    description: str = ""
    created_at: float = 0.0


class TaskListResponse(BaseModel):
    """Response model for /api/tasks endpoint."""

    tasks: List[TaskMetadataResponse] = []
    count: int = 0


class TaskRunResponse(BaseModel):
    """Response model for task execution results."""

    task_id: str = ""
    status: str = "queued"
    message: str = ""


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    detail: Optional[str] = None
    status_code: int = 500