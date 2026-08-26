"""Tests for the scheduler module."""

from __future__ import annotations

import time

from src.core.scheduler import Scheduler, ScheduleEntry


class TestScheduler:
    """Tests for the Scheduler class."""

    def test_schedule_interval(self) -> None:
        sched = Scheduler(tick_interval=0.1)
        entry = sched.schedule_interval(
            entry_id="int-1",
            task_name="periodic.task",
            interval=10.0,
        )
        assert entry.schedule_type == "interval"
        assert entry.interval == 10.0
        assert entry.enabled is True

    def test_schedule_once(self) -> None:
        sched = Scheduler()
        entry = sched.schedule_once(
            entry_id="once-1",
            task_name="delayed.task",
            delay=5.0,
        )
        assert entry.schedule_type == "once"
        assert entry.next_run > time.time()

    def test_schedule_cron(self) -> None:
        sched = Scheduler()
        entry = sched.schedule_cron(
            entry_id="cron-1",
            task_name="cron.task",
            cron_expr="0 * * * *",
        )
        assert entry.schedule_type == "cron"
        assert entry.cron_expr == "0 * * * *"

    def test_cancel(self) -> None:
        sched = Scheduler()
        sched.schedule_interval("to-cancel", "some.task", interval=5.0)
        assert sched.cancel("to-cancel") is True
        assert sched.cancel("to-cancel") is False

    def test_list_entries(self) -> None:
        sched = Scheduler()
        sched.schedule_interval("a", "task.a", 1.0)
        sched.schedule_once("b", "task.b", 2.0)
        entries = sched.list_entries()
        assert len(entries) == 2

    def test_start_stop(self) -> None:
        sched = Scheduler(tick_interval=0.1)
        sched.start()
        assert sched._running is True
        time.sleep(0.2)
        sched.stop()
        assert sched._running is False