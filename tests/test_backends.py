"""Tests for backend abstraction layer."""

from __future__ import annotations

from src.backends.memory import MemoryBackend


class TestMemoryBackend:
    """Tests for the in-memory backend."""

    def test_connect_disconnect(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        assert backend.is_connected()
        backend.disconnect()
        assert not backend.is_connected()

    def test_push_pop(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        backend.push("q1", {"message_id": "m1", "data": "hello"})
        msg = backend.pop("q1")
        assert msg is not None
        assert msg["data"] == "hello"

    def test_pop_empty(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        assert backend.pop("empty") is None

    def test_priority_ordering(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        backend.push("pq", {"message_id": "low"}, priority=1)
        backend.push("pq", {"message_id": "high"}, priority=10)
        msg = backend.pop("pq")
        assert msg is not None
        assert msg["message_id"] == "high"

    def test_peek(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        backend.push("pk", {"message_id": "m1"})
        backend.push("pk", {"message_id": "m2"})
        items = backend.peek("pk", 10)
        assert len(items) == 2
        assert backend.length("pk") == 2

    def test_purge(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        backend.push("pg", {"message_id": "a"})
        backend.push("pg", {"message_id": "b"})
        count = backend.purge("pg")
        assert count == 2
        assert backend.length("pg") == 0

    def test_length(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        assert backend.length("lt") == 0
        backend.push("lt", {"message_id": "x"})
        assert backend.length("lt") == 1

    def test_ack_nack(self) -> None:
        backend = MemoryBackend()
        backend.connect()
        assert backend.ack("q", "m1") is True
        assert backend.nack("q", "m1") is True