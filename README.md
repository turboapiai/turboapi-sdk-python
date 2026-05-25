# TurboAPI SDK (Python)

Python client for calling AI services through [TurboAPI](https://turboapi.ai).

## Installation

```bash
pip install turboapi-sdk
```

## Quick Start

```python
from turboapi import TurboAPIClient

client = TurboAPIClient(api_key="tbp_your_api_key_here")

# Create a task and wait for result
result = client.call.create_and_wait(
    slug_id="karaoke-maker",
    input={
        "audio_file": "https://example.com/song.mp3",
        "task_key": "my-first-task",
    },
    timeout=300,
)
print(f"Task completed! Output: {result.output}")

# Or manage tasks manually
task = client.call.create("some-api", {"key": "value"})
print(f"Task ID: {task.task_id}, Status: {task.status}")

# Poll for updates
updated = client.call.get(task.task_id)
if updated.status.is_terminal:
    print(f"Output: {updated.output}")

# Cancel a queued task
client.call.cancel(task.task_id)

# List your recent tasks
tasks = client.tasks.list(status="succeeded", page=1, page_size=10)
for t in tasks.items:
    print(f"{t.task_id}: {t.name} - {t.status}")
```

## API Reference

### TurboAPIClient

```python
TurboAPIClient(
    api_key: str | None = None,
    *,
    base_url: str = "https://api.turboapi.ai/api/v1",
    timeout: float = 30.0,
)
```

### Call Module (`client.call`)

| Method | Description |
|--------|-------------|
| `create(slug_id, input, *, prefer_wait=False)` | Submit a task |
| `get(task_id)` | Get task status & result |
| `cancel(task_id)` | Cancel a queued task |
| `create_and_wait(slug_id, input, *, timeout=300, poll_interval=2)` | Submit & block until complete |

### Tasks Module (`client.tasks`)

| Method | Description |
|--------|-------------|
| `list(*, status, api_slug, page, page_size)` | List your tasks |
| `get(task_id)` | Get task detail |
| `logs(task_id, *, page, page_size)` | Get execution logs |

## Error Handling

```python
from turboapi import TurboAPIClient
from turboapi.errors import (
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    TimeoutError,
)

client = TurboAPIClient(api_key="...")

try:
    result = client.call.create_and_wait("some-api", {"key": "value"})
except AuthenticationError:
    print("Check your API key")
except RateLimitError as e:
    print(f"Slow down! Retry after {e.retry_after}s")
except NotFoundError:
    print("Task or API not found")
except TimeoutError:
    print("Task did not complete in time")
```

## Task Statuses

| Status | Terminal | Description |
|--------|----------|-------------|
| `pending` | No | Waiting to be queued |
| `queued` | No | In queue awaiting execution |
| `starting` | No | Worker starting up |
| `processing` | No | Execution in progress |
| `succeeded` | Yes | Completed successfully |
| `failed` | Yes | Execution failed |
| `cancelled` | Yes | Cancelled by user |
| `timeout` | Yes | Timed out |
