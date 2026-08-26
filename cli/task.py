"""Task CLI commands: run, list, inspect, cancel."""

from __future__ import annotations

import click


@click.group("task")
def task_group() -> None:
    """Manage and inspect TaskForge tasks."""
    pass


@task_group.command("run")
@click.argument("task_name")
@click.argument("args", nargs=-1)
@click.option("--queue", "-q", default="default", help="Target queue")
@click.option("--priority", "-p", default=0, type=int, help="Task priority")
def run_task(task_name: str, args: tuple, queue: str, priority: int) -> None:
    """Run a task by name with optional positional arguments."""
    from src.core.task import TaskRegistry
    registry = TaskRegistry()
    try:
        metadata = registry.get(task_name)
    except KeyError:
        click.echo(f"Error: Task '{task_name}' not found.", err=True)
        raise SystemExit(1)
    task_id = metadata.func.delay(*args) if hasattr(metadata.func, "delay") else None
    if task_id:
        click.echo(f"Task '{task_name}' queued with id={task_id}")
    else:
        result = metadata.func(*args)
        click.echo(f"Task '{task_name}' executed. Result: {result}")


@task_group.command("list")
def list_tasks() -> None:
    """List all registered tasks with metadata."""
    from src.core.task import TaskRegistry
    registry = TaskRegistry()
    tasks = registry.list_tasks()
    if not tasks:
        click.echo("No tasks registered.")
        return
    click.echo(f"{'Name':<40} {'Queue':<12} {'Pri':<5} {'Retries'}")
    click.echo("-" * 65)
    for t in tasks:
        click.echo(f"{t.name:<40} {t.queue:<12} {t.priority:<5} {t.retries}")


@task_group.command("inspect")
@click.argument("task_name")
def inspect_task(task_name: str) -> None:
    """Show detailed metadata for a task."""
    from src.core.task import TaskRegistry
    registry = TaskRegistry()
    try:
        metadata = registry.get(task_name)
    except KeyError:
        click.echo(f"Error: Task '{task_name}' not found.", err=True)
        raise SystemExit(1)
    info = metadata.to_dict()
    for key, value in info.items():
        click.echo(f"  {key}: {value}")


@task_group.command("cancel")
@click.argument("task_id")
def cancel_task(task_id: str) -> None:
    """Cancel a queued task by its ID."""
    click.echo(f"Cancelling task {task_id}...")
    click.echo("Task cancelled (placeholder implementation).")