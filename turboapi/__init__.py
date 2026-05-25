"""
TurboAPI SDK - Call AI services through the TurboAPI platform.

Usage:
    from turboapi import TurboAPIClient

    client = TurboAPIClient(api_key="tbp_xxxxx")

    # Create a task and wait for result
    result = client.call.create_and_wait(
        slug_id="karaoke-maker",
        input={"audio_file": "https://..."},
        timeout=300,
    )
    print(result.output)
"""

from turboapi.client import TurboAPIClient
from turboapi.models import (
    APIListData,
    APIResponse,
    CategoryResponse,
    TaskResponse,
    TaskLogItem,
    TaskListResponse,
    TaskStatus,
    TaskPriority,
)
from turboapi.errors import (
    TurboAPIError,
    AuthenticationError,
    RateLimitError,
    TaskError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    "TurboAPIClient",
    # Models
    "APIListData",
    "APIResponse",
    "CategoryResponse",
    "TaskResponse",
    "TaskLogItem",
    "TaskListResponse",
    "TaskStatus",
    "TaskPriority",
    # Errors
    "TurboAPIError",
    "AuthenticationError",
    "RateLimitError",
    "TaskError",
    "NotFoundError",
    "ValidationError",
]
