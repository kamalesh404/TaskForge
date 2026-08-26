# Backend Configuration

## Redis

The Redis backend uses sorted sets for priority queues and pub/sub for notifications.

### Setup

```bash
pip install "taskforge[redis]"
```

### Configuration

```yaml
backend:
  type: redis
  url: redis://localhost:6379/0
```

### Features
- Priority queues via sorted sets
- Pub/sub notifications for new tasks
- Atomic operations for concurrent access
- Configurable socket timeout

## RabbitMQ

RabbitMQ provides durable queues with exchanges and bindings.

### Setup

```bash
pip install "taskforge[rabbitmq]"
```

### Configuration

```yaml
backend:
  type: rabbitmq
  url: amqp://guest:guest@localhost:5672/
  exchange: taskforge
```

### Features
- Durable exchanges and queues
- Message acknowledgment
- Priority support via message properties
- Dead letter queue support

## SQLite

Best for local development — no external services needed.

### Configuration

```yaml
backend:
  type: sqlite
  path: taskforge.db
```

### Features
- Thread-safe with per-thread connections
- ACID transactions
- Persistent across restarts
- Zero configuration

## Memory

For testing only — data is lost on restart.

```yaml
backend:
  type: memory
```