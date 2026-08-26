# TaskForge Architecture

## Overview

TaskForge follows a producer-consumer pattern with a pluggable backend layer.

## Components

### Core Layer
- **Task Registry** — Singleton that maps task names to their callable functions and metadata
- **Queue** — Priority queue with enqueue/dequeue semantics backed by pluggable storage
- **Worker** — Process pool executor that consumes from queues and executes tasks
- **Scheduler** — Background thread that dispatches periodic and delayed tasks

### Backend Layer
Each backend implements the `Backend` abstract class:

| Backend | Use Case | Durability |
|---------|----------|------------|
| Redis | Production | Yes |
| RabbitMQ | Production (complex routing) | Yes |
| SQLite | Local development | Yes |
| Memory | Testing | No |

### Monitoring Layer
- **MetricsCollector** — Thread-safe singleton for task execution statistics
- **EventEmitter** — Pub/sub event system for lifecycle hooks
- **HealthChecker** — Heartbeat-based worker health tracking

### Dashboard Layer
FastAPI application providing REST APIs for real-time monitoring.

## Data Flow

```
1. Client calls @task.delay(args)
2. TaskWrapper serializes payload and pushes to Queue
3. Backend stores message (Redis ZADD, RMQ publish, SQLite INSERT)
4. Worker dequeues message via Backend.pop()
5. Worker submits task to ProcessPoolExecutor
6. Task function executes in worker process
7. Results/metrics recorded by MetricsCollector
8. EventEmitter fires task.completed or task.failed
```

## Concurrency Model

Workers use `multiprocessing.ProcessPoolExecutor` for true parallelism.
The main process runs the dequeue loop and dispatches to workers.
Heartbeats and metrics are recorded in separate threads.