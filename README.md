<div align="center">

# 🔥 TaskForge

**A modern distributed task queue for Python**

[![License: MIT](https://img.shields.io/badge/License-MIT-FF4500?style=for-the-badge&logo=mit&logoColor=white)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen?style=for-the-badge&logo=githubactions&logoColor=white)](.github/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)
[![Code style: ruff](https://img.shields.io/badge/Code_Style-Ruff-000000?style=for-the-badge&logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)

<br/>

**TaskForge** is a lightweight, fast, and developer-friendly task queue built in Python. Schedule jobs, retry failed tasks, monitor workers — all from a clean CLI or Python API.

[Getting Started](#-quick-start) • [Features](#-features) • [Architecture](#-architecture) • [Backends](#-backends) • [CLI](#-cli-reference) • [API](#-python-api) • [Dashboard](#-dashboard) • [Contributing](#-contributing)

---

</div>

## ⚡ Quick Start

```bash
# Install
pip install taskforge

# Start a worker
taskforge worker start --queue default

# Run a task
taskforge task run my_module.my_task --args '{"user_id": 42}'

# Check status
taskforge queue stats
```

### Python API

```python
from taskforge import Queue, task

# Define a task
@task(name="send_email", max_retries=3, retry_delay=60)
def send_email(user_id: int, subject: str):
    # Send email logic here
    print(f"Email sent to user {user_id}")

# Enqueue tasks
queue = Queue(backend="redis://localhost:6379")
queue.enqueue(send_email, user_id=42, subject="Welcome!")
queue.enqueue(send_email, user_id=43, subject="Hello!")

# Delayed execution
queue.enqueue_in(300, send_email, user_id=44, subject="Follow-up")

# Cron scheduling
queue.enqueue_cron("0 9 * * *", send_email, user_id=42, subject="Daily digest")
```

---

## 🚀 Features

<table>
<tr>
<td>

### ⚙️ Core Engine
- **Task decorator** with automatic registration
- **Priority queues** (critical, high, normal, low)
- **Delayed execution** with `enqueue_in()`
- **Cron scheduling** for recurring tasks
- **Task chaining** — run tasks in sequence

</td>
<td>

### 🔄 Reliability
- **Configurable retries** — fixed, exponential, or jitter backoff
- **Dead letter queue** for permanently failed tasks
- **Graceful shutdown** with signal handling
- **Heartbeat monitoring** for worker health
- **Automatic task serialization**

</td>
</tr>
<tr>
<td>

### 🎯 Developer Experience
- **Clean Python API** — no boilerplate
- **CLI for everything** — workers, tasks, queues
- **Type hints** throughout the codebase
- **Rich logging** with structured output
- **Docker ready** — one command to deploy

</td>
<td>

### 📊 Observability
- **Real-time dashboard** with metrics
- **Task execution timeline**
- **Worker status monitoring**
- **Queue depth and throughput**
- **Event system** for lifecycle hooks

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TaskForge Architecture                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ Producer │───▶│  Queue   │◀───│ Consumer │          │
│  │ (Client) │    │ (Backend)│    │ (Worker) │          │
│  └──────────┘    └────┬─────┘    └────┬─────┘          │
│                       │               │                 │
│                       ▼               ▼                 │
│              ┌──────────────┐  ┌──────────────┐        │
│              │   Redis /    │  │   Process    │        │
│              │  RabbitMQ /  │  │    Pool      │        │
│              │   SQLite     │  │  (N workers) │        │
│              └──────────────┘  └──────────────┘        │
│                       │               │                 │
│                       ▼               ▼                 │
│              ┌──────────────┐  ┌──────────────┐        │
│              │  Scheduler   │  │  Monitoring  │        │
│              │  (Cron/Delay)│  │  (Metrics)   │        │
│              └──────────────┘  └──────────────┘        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Project Structure

```
TaskForge/
├── src/
│   ├── core/           # Task engine, queue, worker, scheduler
│   ├── backends/       # Redis, RabbitMQ, SQLite, Memory
│   ├── monitoring/     # Metrics, events, health checks
│   ├── dashboard/      # FastAPI web dashboard
│   ├── serialization/  # JSON, pickle, msgpack + compression
│   ├── cli/            # Click CLI commands
│   └── utils/          # Logging, config, signals
├── tests/              # pytest test suite
├── docs/               # Documentation
├── Dockerfile          # Container build
└── docker-compose.yml  # Full stack deployment
```

---

## 🔌 Backends

| Backend | Use Case | Setup |
|---------|----------|-------|
| **Redis** | Production — fast, pub/sub support | `Queue(backend="redis://localhost:6379")` |
| **RabbitMQ** | Production — reliable messaging | `Queue(backend="amqp://guest:guest@localhost")` |
| **SQLite** | Development — zero config | `Queue(backend="sqlite:///tasks.db")` |
| **Memory** | Testing — ephemeral | `Queue(backend="memory://")` |

### Redis Backend

```python
from taskforge.backends import RedisBackend

backend = RedisBackend(
    host="localhost",
    port=6379,
    db=0,
    password=None,
    ssl=False,
)
queue = Queue(backend=backend)
```

### RabbitMQ Backend

```python
from taskforge.backends import RabbitMQBackend

backend = RabbitMQBackend(
    host="localhost",
    port=5672,
    username="guest",
    password="guest",
    vhost="/",
)
queue = Queue(backend=backend)
```

---

## 💻 CLI Reference

### Worker Management

```bash
# Start a worker
taskforge worker start --queue default --concurrency 4

# List active workers
taskforge worker list

# Check worker status
taskforge worker status <worker-id>

# Stop a worker
taskforge worker stop <worker-id>
```

### Task Operations

```bash
# Run a task immediately
taskforge task run my_module.my_task --args '{"key": "value"}'

# List registered tasks
taskforge task list

# Inspect a task
taskforge task inspect <task-id>

# Cancel a running task
taskforge task cancel <task-id>
```

### Queue Management

```bash
# View queue stats
taskforge queue stats

# Peek at next tasks
taskforge queue peek --limit 10

# Purge a queue
taskforge queue purge <queue-name>
```

---

## 📊 Dashboard

TaskForge includes a built-in web dashboard for monitoring:

```bash
# Start the dashboard
taskforge dashboard --port 8080
```

### Features
- **Task overview** — total, running, completed, failed
- **Worker status** — live health and utilization
- **Queue depth** — real-time metrics per queue
- **Task timeline** — execution history and duration
- **Filter by status** — quickly find failed tasks

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test
pytest tests/test_task.py -v
```

---

## 🐳 Docker

```bash
# Build
docker build -t taskforge .

# Run worker
docker run -e REDIS_URL=redis://redis:6379 taskforge worker start

# Full stack with docker-compose
docker-compose up -d
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    command: taskforge worker start --queue default
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  dashboard:
    build: .
    command: taskforge dashboard --port 8080
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting_started.md) | Installation and first steps |
| [Architecture](docs/architecture.md) | System design and internals |
| [Backends](docs/backends.md) | Backend configuration guide |
| [Scheduling](docs/scheduling.md) | Cron and delayed tasks |
| [API Reference](docs/api_reference.md) | Complete Python API docs |

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Clone
git clone https://github.com/kamalesh404/TaskForge.git

# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check src/ tests/

# Run tests
pytest
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ by [Kamalesh](https://github.com/kamalesh404)**

[![Follow](https://img.shields.io/badge/Follow-kamalesh404-1DA1F2?style=for-the-badge&logo=github&logoColor=white)](https://github.com/kamalesh404)

</div>
