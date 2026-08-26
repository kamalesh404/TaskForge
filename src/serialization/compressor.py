"""Compression utilities: gzip and lz4."""

from __future__ import annotations

import gzip
import io
from abc import ABC, abstractmethod
from typing import Optional


class Compressor(ABC):
    """Abstract base class for compressors."""

    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        """Compress raw bytes."""
        ...

    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        """Decompress compressed bytes."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this compressor."""
        ...


class GzipCompressor(Compressor):
    """Compress using gzip — available everywhere, decent ratio."""

    def __init__(self, level: int = 6) -> None:
        self.level = level

    def compress(self, data: bytes) -> bytes:
        return gzip.compress(data, compresslevel=self.level)

    def decompress(self, data: bytes) -> bytes:
        return gzip.decompress(data)

    @property
    def name(self) -> str:
        return "gzip"


class LZ4Compressor(Compressor):
    """Compress using lz4 — very fast, good ratio."""

    def compress(self, data: bytes) -> bytes:
        try:
            import lz4.frame
            return lz4.frame.compress(data)
        except ImportError:
            raise ImportError("Install lz4: pip install lz4>=4.0")

    def decompress(self, data: bytes) -> bytes:
        try:
            import lz4.frame
            return lz4.frame.decompress(data)
        except ImportError:
            raise ImportError("Install lz4: pip install lz4>=4.0")

    @property
    def name(self) -> str:
        return "lz4"


class NullCompressor(Compressor):
    """No-op compressor for when compression is not needed."""

    def compress(self, data: bytes) -> bytes:
        return data

    def decompress(self, data: bytes) -> bytes:
        return data

    @property
    def name(self) -> str:
        return "none"


_COMPRESSORS = {
    "gzip": lambda: GzipCompressor(),
    "lz4": lambda: LZ4Compressor(),
    "none": lambda: NullCompressor(),
}


def get_compressor(name: Optional[str] = None) -> Compressor:
    """Factory that returns a compressor by name. None returns no compression."""
    if name is None or name == "none":
        return NullCompressor()
    factory = _COMPRESSORS.get(name)
    if factory is None:
        raise ValueError(f"Unknown compressor '{name}'. Available: {list(_COMPRESSORS)}")
    return factory()


def compress_data(data: bytes, compressor_name: Optional[str] = None) -> bytes:
    """Convenience function to compress data with a named compressor."""
    compressor = get_compressor(compressor_name)
    return compressor.compress(data)


def decompress_data(data: bytes, compressor_name: Optional[str] = None) -> bytes:
    """Convenience function to decompress data with a named compressor."""
    compressor = get_compressor(compressor_name)
    return compressor.decompress(data)