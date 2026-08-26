"""Click CLI entry point for TaskForge."""

from __future__ import annotations

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="TaskForge")
def cli() -> None:
    """TaskForge — Distributed task queue for Python."""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Dashboard host")
@click.option("--port", default=8000, type=int, help="Dashboard port")
@click.option("--backend-url", envvar="TASKFORGE_REDIS_URL", default="redis://localhost:6379")
def dashboard(host: str, port: int, backend_url: str) -> None:
    """Start the monitoring dashboard."""
    click.echo(f"Starting TaskForge Dashboard on {host}:{port}")
    from src.dashboard.app import run_dashboard
    run_dashboard(host=host, port=port)


@cli.command()
def status() -> None:
    """Show overall system status."""
    from src.core.task import TaskRegistry
    from src.monitoring.metrics import MetricsCollector
    from src.monitoring.health import HealthChecker

    registry = TaskRegistry()
    metrics = MetricsCollector()
    workers = HealthChecker.get_all_statuses()
    overview = metrics.get_overview()

    click.echo("=== TaskForge Status ===")
    click.echo(f"Registered tasks: {len(registry.list_tasks())}")
    click.echo(f"Total executions:  {overview['total_tasks']}")
    click.echo(f"  Successes:       {overview['total_success']}")
    click.echo(f"  Failures:        {overview['total_failure']}")
    click.echo(f"Active workers:    {len(workers)}")
    for w in workers:
        click.echo(f"  {w['worker_id']} — {w['status']} (completed={w['tasks_completed']})")


@cli.command()
def tasks() -> None:
    """List all registered tasks."""
    from src.core.task import TaskRegistry
    registry = TaskRegistry()
    task_list = registry.list_tasks()
    if not task_list:
        click.echo("No tasks registered.")
        return
    click.echo(f"{'Name':<40} {'Queue':<15} {'Retries':<8}")
    click.echo("-" * 63)
    for t in task_list:
        click.echo(f"{t.name:<40} {t.queue:<15} {t.retries:<8}")


if __name__ == "__main__":
    cli()