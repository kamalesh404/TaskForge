"""Task decorator, task registry, and task metadata."""

from __future__ import annotations

import functools
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class TaskMetadata:
    """Metadata attached to every registered task."""

    name: str
    func: Callable[..., Any]
    queue: str = "default"
    priority: int = 0
    retries: int = 0
    timeout: Optional[int] = None
    description: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "queue": self.queue,
            "priority": self.priority,
            "retries": self.retries,
            "timeout": self.timeout,
            "description": self.description,
            "created_at": self.created_at,
        }


class TaskRegistry:
    """Global registry that maps task names to their metadata."""

    _instance: Optional[TaskRegistry] = None
    _tasks: Dict[str, TaskMetadata] = {}

    def __new__(cls) -> TaskRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tasks = {}
        return cls._instance

    def register(self, metadata: TaskMetadata) -> None:
        if metadata.name in self._tasks:
            raise ValueError(f"Task '{metadata.name}' is already registered")
        self._tasks[metadata.name] = metadata

    def get(self, name: str) -> TaskMetadata:
        if name not in self._tasks:
            raise KeyError(f"Task '{name}' not found in registry")
        return self._tasks[name]

    def list_tasks(self) -> list[TaskMetadata]:
        return list(self._tasks.values())

    def remove(self, name: str) -> None:
        self._tasks.pop(name, None)

    def clear(self) -> None:
        self._tasks.clear()


class TaskWrapper:
    """Wraps a callable so it can be dispatched via ``.delay()``."""

    def __init__(self, func: Callable[..., Any], metadata: TaskMetadata) -> None:
        self.func = func
        self.metadata = metadata
        functools.update_wrapper(self, func)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)

    def delay(self, *args: Any, **kwargs: Any) -> str:
        """Enqueue the task for async execution and return a task ID."""
        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "task_name": self.metadata.name,
            "args": args,
            "kwargs": kwargs,
            "queued_at": time.time(),
        }
        _pending_tasks.append(payload)
        return task_id

    def apply(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the task synchronously (useful for testing)."""
        return self.func(*args, **kwargs)


_pending_tasks: list[Dict[str, Any]] = []


def get_pending_tasks() -> list[Dict[str, Any]]:
    """Return and clear pending tasks (used by queue backend)."""
    tasks = list(_pending_tasks)
    _pending_tasks.clear()
    return tasks


def task(
    name: Optional[str] = None,
    queue: str = "default",
    priority: int = 0,
    retries: int = 0,
    timeout: Optional[int] = None,
    description: str = "",
) -> Callable[[Callable[..., Any]], TaskWrapper]:
    """Decorator that registers a function as a TaskForge task."""

    def decorator(func: Callable[..., Any]) -> TaskWrapper:
        task_name = name or f"{func.__module__}.{func.__qualname__}"
        metadata = TaskMetadata(
            name=task_name,
            func=func,
            queue=queue,
            priority=priority,
            retries=retries,
            timeout=timeout,
            description=description or func.__doc__ or "",
        )
        registry = TaskRegistry()
        registry.register(metadata)
        wrapper = TaskWrapper(func, metadata)
        return wrapper

    return decorator