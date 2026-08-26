# API Reference

## Core

### `task(name, queue, priority, retries, timeout, description)`

Decorator that registers a function as a TaskForge task.

- `name` — Unique task identifier (default: module.qualname)
- `queue` — Queue name (default: "default")
- `priority` — Integer priority, higher = dequeued first
- `retries` — Number of automatic retries on failure
- `timeout` — Maximum execution time in seconds
- `description` — Human-readable description

### `Queue(name, backend)`

Task queue backed by a pluggable backend.

- `enqueue(task_name, payload, priority, delay_seconds) -> str`
- `dequeue(timeout) -> Optional[QueueMessage]`
- `peek(count) -> List[QueueMessage]`
- `size() -> int`
- `purge() -> int`
- `stats() -> Dict[str, Any]`

### `Worker(queue, count, timeout, backend_url)`

Multi-process task executor.

- `start()` — Begin consuming tasks
- `stop()` — Graceful shutdown
- `register_signals()` — Handle SIGINT/SIGTERM
- `stats` — Property with current metrics

### `Scheduler(tick_interval)`

Background task scheduler.

- `schedule_interval(entry_id, task_name, interval, args, kwargs)`
- `schedule_once(entry_id, task_name, delay, args, kwargs)`
- `schedule_cron(entry_id, task_name, cron_expr, args, kwargs)`
- `cancel(entry_id) -> bool`
- `start()` / `stop()`

## Backends

### `Backend` (abstract)

- `connect()` / `disconnect()`
- `push(queue_name, message, priority)`
- `pop(queue_name) -> Optional[Dict]`
- `peek(queue_name, count) -> List[Dict]`
- `length(queue_name) -> int`
- `purge(queue_name) -> int`
- `ack(queue_name, message_id) -> bool`
- `nack(queue_name, message_id) -> bool`

## Monitoring

### `MetricsCollector`

- `record(task_name, status, elapsed, error, worker_id)`
- `get_task_stats(task_name) -> Dict`
- `get_overview() -> Dict`
- `get_recent(count) -> List[Dict]`

### `EventEmitter`

- `on(event, callback)` / `off(event, callback)`
- `emit(event, data)`
- `get_history(event, count) -> List[Dict]`

### `HealthChecker(worker_id)`

- `start_heartbeat()` / `stop_heartbeat()`
- `record_task_dispatched(task_name)`
- `record_task_completed(result)`
- `get_all_statuses() -> List[Dict]` (classmethod)