"""JSON, pickle, and msgpack serialization strategies."""

from __future__ import annotations

import json
import pickle
from abc import ABC, abstractmethod
from typing import Any


class Serializer(ABC):
    """Abstract base class for all serializers."""

    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        """Convert a Python object to bytes."""
        ...

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """Convert bytes back to a Python object."""
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Return the MIME content type for this serializer."""
        ...


class JSONSerializer(Serializer):
    """Serialize using the built-in json module."""

    def __init__(self, indent: bool = False, sort_keys: bool = True) -> None:
        self.indent = indent
        self.sort_keys = sort_keys

    def serialize(self, data: Any) -> bytes:
        return json.dumps(
            data,
            indent=2 if self.indent else None,
            sort_keys=self.sort_keys,
            default=str,
        ).encode("utf-8")

    def deserialize(self, data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))

    @property
    def content_type(self) -> str:
        return "application/json"


class PickleSerializer(Serializer):
    """Serialize using Python pickle — faster but not cross-language."""

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL) -> None:
        self.protocol = protocol

    def serialize(self, data: Any) -> bytes:
        return pickle.dumps(data, protocol=self.protocol)

    def deserialize(self, data: bytes) -> Any:
        return pickle.loads(data)  # noqa: S301 — intentional pickle use

    @property
    def content_type(self) -> str:
        return "application/octet-stream"


class MsgPackSerializer(Serializer):
    """Serialize using msgpack for compact binary encoding."""

    def serialize(self, data: Any) -> bytes:
        try:
            import msgpack
            return msgpack.packb(data, use_bin_type=True)
        except ImportError:
            raise ImportError("Install msgpack: pip install msgpack>=1.0")

    def deserialize(self, data: bytes) -> Any:
        try:
            import msgpack
            return msgpack.unpackb(data, raw=False)
        except ImportError:
            raise ImportError("Install msgpack: pip install msgpack>=1.0")

    @property
    def content_type(self) -> str:
        return "application/msgpack"


_SERIALIZERS = {
    "json": lambda: JSONSerializer(),
    "pickle": lambda: PickleSerializer(),
    "msgpack": lambda: MsgPackSerializer(),
}


def get_serializer(name: str = "json") -> Serializer:
    """Factory that returns a serializer by name."""
    factory = _SERIALIZERS.get(name)
    if factory is None:
        raise ValueError(f"Unknown serializer '{name}'. Available: {list(_SERIALIZERS)}")
    return factory()