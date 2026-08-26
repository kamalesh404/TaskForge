"""Test fixtures for TaskForge."""

from __future__ import annotations

import pytest

from src.backends.memory import MemoryBackend
from src.core.queue import Queue
from src.core.task import TaskRegistry


@pytest.fixture
def memory_backend() -> MemoryBackend:
    """Return a connected in-memory backend."""
    backend = MemoryBackend()
    backend.connect()
    yield backend
    backend.disconnect()


@pytest.fixture
def queue(memory_backend: MemoryBackend) -> Queue:
    """Return a Queue backed by the memory backend."""
    return Queue(name="test_queue", backend=memory_backend)


@pytest.fixture(autouse=True)
def clean_registry() -> None:
    """Clear the task registry before each test."""
    registry = TaskRegistry()
    registry.clear()
    yield
    registry.clear()