"""Tests for task registration and execution."""

from __future__ import annotations

import pytest
from src.core.task import TaskRegistry, TaskMetadata, task, get_pending_tasks


class TestTaskRegistry:
    """Tests for the TaskRegistry singleton."""

    def test_register_and_get(self) -> None:
        registry = TaskRegistry()
        meta = TaskMetadata(name="test.foo", func=lambda: None)
        registry.register(meta)
        result = registry.get("test.foo")
        assert result.name == "test.foo"

    def test_duplicate_raises(self) -> None:
        registry = TaskRegistry()
        meta = TaskMetadata(name="dup.task", func=lambda: None)
        registry.register(meta)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(meta)

    def test_get_missing_raises(self) -> None:
        registry = TaskRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent.task")

    def test_list_tasks(self) -> None:
        registry = TaskRegistry()
        registry.register(TaskMetadata(name="a", func=lambda: None))
        registry.register(TaskMetadata(name="b", func=lambda: None))
        tasks = registry.list_tasks()
        assert len(tasks) == 2

    def test_remove(self) -> None:
        registry = TaskRegistry()
        registry.register(TaskMetadata(name="removable", func=lambda: None))
        registry.remove("removable")
        with pytest.raises(KeyError):
            registry.get("removable")

    def test_clear(self) -> None:
        registry = TaskRegistry()
        registry.register(TaskMetadata(name="x", func=lambda: None))
        registry.clear()
        assert len(registry.list_tasks()) == 0


class TestTaskDecorator:
    """Tests for the @task() decorator."""

    def test_decorator_registers_task(self) -> None:
        @task(name="unit.test_task", queue="testing")
        def my_task(x: int) -> int:
            return x * 2

        registry = TaskRegistry()
        meta = registry.get("unit.test_task")
        assert meta.queue == "testing"

    def test_decorator_preserves_function(self) -> None:
        @task(name="call.test")
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5

    def test_delay_enqueues(self) -> None:
        @task(name="delay.test")
        def delayed_task(x: int) -> int:
            return x

        task_id = delayed_task.delay(42)
        pending = get_pending_tasks()
        assert len(pending) >= 1
        assert pending[-1]["task_name"] == "delay.test"
        assert pending[-1]["args"] == (42,)

    def test_apply_executes_synchronously(self) -> None:
        @task(name="apply.test")
        def compute(n: int) -> int:
            return n ** 2

        result = compute.apply(5)
        assert result == 25