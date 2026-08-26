"""Queue CLI commands: peek, purge, stats."""

from __future__ import annotations

import click


@click.group("queue")
def queue_group() -> None:
    """Manage TaskForge queues."""
    pass


@queue_group.command("peek")
@click.argument("queue_name", default="default")
@click.option("--count", "-n", default=10, type=int, help="Number of messages to peek")
def peek_queue(queue_name: str, count: int) -> None:
    """Peek at messages in a queue without removing them."""
    from src.core.queue import Queue
    q = Queue(name=queue_name)
    messages = q.peek(count=count)
    if not messages:
        click.echo(f"Queue '{queue_name}' is empty.")
        return
    click.echo(f"Queue '{queue_name}' — {len(messages)} message(s):")
    for msg in messages:
        click.echo(
            f"  id={msg.message_id}  task={msg.task_name}  "
            f"priority={msg.priority}  attempts={msg.attempts}"
        )


@queue_group.command("purge")
@click.argument("queue_name", default="default")
@click.confirmation_option(prompt="Are you sure you want to purge this queue?")
def purge_queue(queue_name: str) -> None:
    """Remove all messages from a queue."""
    from src.core.queue import Queue
    q = Queue(name=queue_name)
    count = q.purge()
    click.echo(f"Purged {count} message(s) from '{queue_name}'.")


@queue_group.command("stats")
@click.argument("queue_name", default="default")
def queue_stats(queue_name: str) -> None:
    """Show statistics for a queue."""
    from src.core.queue import Queue
    q = Queue(name=queue_name)
    stats = q.stats()
    click.echo(f"Queue: {stats['queue_name']}")
    click.echo(f"  Depth:   {stats['depth']}")
    click.echo(f"  Backend: {stats['backend']}")