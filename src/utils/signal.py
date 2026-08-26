"""Signal handling for graceful shutdown of workers."""

from __future__ import annotations

import logging
import signal
import sys
from typing import Callable, Optional

logger = logging.getLogger("taskforge.signal")


def setup_signal_handlers(
    shutdown_fn: Callable[[Optional[int], Optional[object]], None],
) -> None:
    """Register signal handlers that call shutdown_fn on SIGINT/SIGTERM."""
    def _handler(signum: int, frame: object) -> None:
        sig_name = signal.Signals(signum).name
        logger.info("Received signal %s — initiating shutdown", sig_name)
        shutdown_fn(signum, frame)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)
    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, _handler)
    logger.debug("Signal handlers registered")


def ignore_sigpipe() -> None:
    """Ignore SIGPIPE to prevent crashes on broken pipe writes."""
    if sys.platform != "win32":
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)


def setup_alarm_handler(interval: float, callback: Callable[[int], None]) -> None:
    """Set up a repeating alarm for periodic housekeeping."""
    def _alarm_handler(signum: int, frame: object) -> None:
        callback(signum)
        signal.alarm(int(interval))

    if sys.platform != "win32":
        signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(int(interval))


def reset_signals() -> None:
    """Reset all signal handlers to their default values."""
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, signal.SIG_DFL)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
    logger.debug("Signal handlers reset to defaults")