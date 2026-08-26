# Getting Started with TaskForge

## Installation

```bash
pip install taskforge
```

For full features with all backends:

```bash
pip install "taskforge[redis,rabbitmq,dashboard,msgpack,lz4]"
```

## Your First Task

Create a file `tasks.py`:

```python
from src.core.task import task

@task(name="send_welcome_email", queue="emails", retries=3)
def send_welcome_email(user_id: int, email: str) -> dict:
    """Send a welcome email to a new user."""
    # Your email logic here
    print(f"Sending welcome email to {email}")
    return {"status": "sent", "user_id": user_id}
```

## Enqueue Tasks

```python
# Enqueue for async execution
task_id = send_welcome_email.delay(user_id=42, email="alice@example.com")
print(f"Task queued: {task_id}")

# Execute synchronously (useful in tests)
result = send_welcome_email.apply(user_id=42, email="alice@example.com")
```

## Start a Worker

```bash
# In-memory (development)
taskforge worker start --backend memory://

# Redis
taskforge worker start --backend redis://localhost:6379

# With 8 workers
taskforge worker start --backend redis://localhost:6379 --count 8
```

## Monitor with Dashboard

```bash
taskforge dashboard start --port 8000
# Open http://localhost:8000 in your browser
```

## Next Steps

- Read [Architecture](architecture.md) for system design details
- Read [Backends](backends.md) for backend configuration
- Read [Scheduling](scheduling.md) for cron and delayed tasks