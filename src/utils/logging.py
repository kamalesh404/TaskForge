"""Structured logging configuration for TaskForge."""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter for production environments."""

    def __init__(self, service_name: str = "taskforge") -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry["extra"] = record.extra_data
        return json.dumps(log_entry, default=str)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = time.strftime("%H:%M:%S", time.localtime(record.created))
        msg = f"{color}{ts} [{record.levelname:8s}]{self.RESET} {record.name}: {record.getMessage()}"
        if record.exc_info and record.exc_info[0]:
            msg += f"\n{self.formatException(record.exc_info)}"
        return msg


def setup_logging(
    level: str = "INFO",
    structured: bool = False,
    service_name: str = "taskforge",
) -> None:
    """Configure TaskForge logging with the appropriate formatter."""
    root = logging.getLogger("taskforge")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    if structured:
        handler.setFormatter(StructuredFormatter(service_name=service_name))
    else:
        handler.setFormatter(HumanFormatter())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the taskforge namespace."""
    return logging.getLogger(f"taskforge.{name}")