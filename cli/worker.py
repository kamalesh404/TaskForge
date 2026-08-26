"""Worker CLI commands: start, stop, list, status."""

from __future__ import annotations

import click


@click.group("worker")
def worker_group() -> None:
    """Manage TaskForge workers."""
    pass


@worker_group.command("start")
@click.option("--backend", default="memory://", help="Backend URL (e.g. redis://localhost:6379)")
@click.option("--count", "-n", default=4, type=int, help="Number of worker processes")
@click.option("--timeout", default=300, type=int, help="Task timeout in seconds")
@click.option("--queue", "-q", default="default", help="Queue name to consume from")
def start_worker(backend: str, count: int, timeout: int, queue: str) -> None:
    """Start worker processes to consume tasks."""
    click.echo(f"Starting {count} worker(s) on queue '{queue}' with backend {backend}")
    from src.backends.memory import MemoryBackend
    from src.core.queue import Queue
    from src.core.worker import Worker
    from src.utils.signal import setup_signal_handlers

    memory = MemoryBackend()
    memory.connect()
    q = Queue(name=queue, backend=memory)
    worker = Worker(queue=q, count=count, timeout=timeout)
    worker.register_signals()
    setup_signal_handlers(worker.stop)
    click.echo("Workers started. Press Ctrl+C to stop.")
    worker.start()


@worker_group.command("stop")
@click.argument("worker_id", required=False)
def stop_worker(worker_id: str | None) -> None:
    """Stop a running worker (by PID or all)."""
    click.echo(f"Stopping worker(s)...")


@worker_group.command("list")
def list_workers() -> None:
    """List active workers."""
    from src.monitoring.health import HealthChecker
    statuses = HealthChecker.get_all_statuses()
    if not statuses:
        click.echo("No active workers.")
        return
    for w in statuses:
        click.echo(
            f"  {w['worker_id']}  pid={w['pid']}  "
            f"status={w['status']}  completed={w['tasks_completed']}"
        )


@worker_group.command("status")
@click.argument("worker_id", required=False)
def worker_status(worker_id: str | None) -> None:
    """Show detailed status for a worker."""
    from src.monitoring.health import HealthChecker
    statuses = HealthChecker.get_all_statuses()
    for w in statuses:
        if worker_id is None or w["worker_id"] == worker_id:
            click.echo(f"Worker: {w['worker_id']}")
            click.echo(f"  PID:         {w['pid']}")
            click.echo(f"  Status:      {w['status']}")
            click.echo(f"  Uptime:      {w['uptime']:.0f}s")
            click.echo(f"  Completed:   {w['tasks_completed']}")
            click.echo(f"  Failed:      {w['tasks_failed']}")
            click.echo(f"  Current:     {w['current_task'] or 'idle'}")