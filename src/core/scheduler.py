"""Cron scheduler for periodic and delayed task execution."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("taskforge.scheduler")


@dataclass
class ScheduleEntry:
    """A single scheduled task entry."""

    entry_id: str
    task_name: str
    schedule_type: str  # "interval", "cron", "once"
    interval: float = 0.0
    cron_expr: str = ""
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run: float = 0.0
    next_run: float = 0.0
    run_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "task_name": self.task_name,
            "schedule_type": self.schedule_type,
            "interval": self.interval,
            "cron_expr": self.cron_expr,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
        }


class Scheduler:
    """Manages periodic and delayed task scheduling."""

    def __init__(self, tick_interval: float = 1.0) -> None:
        self.tick_interval = tick_interval
        self._entries: Dict[str, ScheduleEntry] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._dispatch_fn: Optional[Callable[[str, tuple, dict], None]] = None

    def set_dispatch(self, fn: Callable[[str, tuple, dict], None]) -> None:
        """Set the function called to actually execute a scheduled task."""
        self._dispatch_fn = fn

    def schedule_interval(
        self,
        entry_id: str,
        task_name: str,
        interval: float,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> ScheduleEntry:
        """Schedule a task to run at a fixed interval in seconds."""
        entry = ScheduleEntry(
            entry_id=entry_id,
            task_name=task_name,
            schedule_type="interval",
            interval=interval,
            args=args,
            kwargs=kwargs or {},
            next_run=time.time() + interval,
        )
        self._entries[entry_id] = entry
        logger.info("Scheduled interval task %s every %.1fs", task_name, interval)
        return entry

    def schedule_once(
        self,
        entry_id: str,
        task_name: str,
        delay: float,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> ScheduleEntry:
        """Schedule a one-shot delayed task."""
        entry = ScheduleEntry(
            entry_id=entry_id,
            task_name=task_name,
            schedule_type="once",
            args=args,
            kwargs=kwargs or {},
            next_run=time.time() + delay,
        )
        self._entries[entry_id] = entry
        logger.info("Scheduled one-shot task %s in %.1fs", task_name, delay)
        return entry

    def schedule_cron(
        self,
        entry_id: str,
        task_name: str,
        cron_expr: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> ScheduleEntry:
        """Schedule a task with a cron expression (simplified)."""
        entry = ScheduleEntry(
            entry_id=entry_id,
            task_name=task_name,
            schedule_type="cron",
            cron_expr=cron_expr,
            args=args,
            kwargs=kwargs or {},
            next_run=time.time() + 60,
        )
        self._entries[entry_id] = entry
        logger.info("Scheduled cron task %s: %s", task_name, cron_expr)
        return entry

    def cancel(self, entry_id: str) -> bool:
        """Cancel a scheduled entry. Returns True if found."""
        entry = self._entries.pop(entry_id, None)
        if entry:
            logger.info("Cancelled schedule %s", entry_id)
            return True
        return False

    def list_entries(self) -> List[ScheduleEntry]:
        return list(self._entries.values())

    def start(self) -> None:
        """Start the scheduler in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Scheduler started with tick_interval=%.1fs", self.tick_interval)

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _run_loop(self) -> None:
        """Main scheduling loop."""
        while self._running:
            now = time.time()
            for entry in list(self._entries.values()):
                if not entry.enabled or entry.next_run > now:
                    continue
                self._execute_entry(entry)
            time.sleep(self.tick_interval)

    def _execute_entry(self, entry: ScheduleEntry) -> None:
        """Execute a schedule entry and reschedule if needed."""
        entry.last_run = time.time()
        entry.run_count += 1
        logger.info("Executing scheduled task %s", entry.task_name)
        if self._dispatch_fn:
            self._dispatch_fn(entry.task_name, entry.args, entry.kwargs)
        if entry.schedule_type == "interval":
            entry.next_run = time.time() + entry.interval
        elif entry.schedule_type == "once":
            entry.enabled = False
        elif entry.schedule_type == "cron":
            entry.next_run = time.time() + 60  # Simplified