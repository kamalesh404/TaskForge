# Scheduling

## Interval Tasks

Run a task at a fixed interval:

```python
from src.core.scheduler import Scheduler

scheduler = Scheduler()
scheduler.schedule_interval(
    entry_id="cleanup",
    task_name="cleanup_temp_files",
    interval=3600,  # every hour
    args=("/tmp",),
)
scheduler.start()
```

## Delayed Tasks

Schedule a one-shot task with a delay:

```python
scheduler.schedule_once(
    entry_id="reminder",
    task_name="send_reminder",
    delay=1800,  # 30 minutes from now
    args=(user_id,),
)
```

## Cron Tasks

Use simplified cron expressions (minute granularity):

```python
scheduler.schedule_cron(
    entry_id="hourly-report",
    task_name="generate_report",
    cron_expr="0 * * * *",  # every hour at :00
)
```

## Using the Task Decorator

```python
@task(name="periodic_sync", queue="sync")
def sync_data(source: str) -> bool:
    return True

# Schedule from application startup
scheduler = Scheduler()
scheduler.schedule_interval("sync-loop", "periodic_sync", 300, args=("main-db",))
```

## Dispatcher Integration

The scheduler calls a dispatch function to execute tasks:

```python
def my_dispatch(task_name: str, args: tuple, kwargs: dict) -> None:
    registry = TaskRegistry()
    metadata = registry.get(task_name)
    metadata.func(*args, **kwargs)

scheduler.set_dispatch(my_dispatch)
```