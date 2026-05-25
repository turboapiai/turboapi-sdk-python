"""
Data models for the TurboAPI SDK.

These mirror the backend schemas but are SDK-specific,
not tied to backend implementation details.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Task status enum matching backend TaskStatus."""

    PENDING = "pending"
    QUEUED = "queued"
    STARTING = "starting"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal (non-transient) status."""
        return self in {
            TaskStatus.SUCCEEDED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        }

    @property
    def is_active(self) -> bool:
        """Check if the task is still being processed."""
        return self in {
            TaskStatus.QUEUED,
            TaskStatus.STARTING,
            TaskStatus.PROCESSING,
        }


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskLogItem:
    """A single log entry for a task."""

    timestamp: str
    level: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class TaskResponse:
    """Full task response with status and optional output."""

    id: str
    task_id: str
    name: str
    status: Optional[TaskStatus] = None
    progress: int = 0
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    message: Optional[str] = None
    error_message: Optional[str] = None
    output: Optional[Any] = None
    api_slug: Optional[str] = None
    priority: Optional[str] = None
    prediction_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    logs: Optional[List[TaskLogItem]] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "TaskResponse":
        """Create from API response dict (data field)."""
        status_raw = data.get("status")
        status = TaskStatus(status_raw) if status_raw else None

        logs_raw = data.get("logs")
        logs = None
        if logs_raw:
            logs = [
                TaskLogItem(
                    timestamp=log["timestamp"],
                    level=log["level"],
                    message=log["message"],
                    details=log.get("details"),
                )
                for log in logs_raw
            ]

        for dt_field in ("created_at", "started_at", "completed_at", "expires_at"):
            val = data.get(dt_field)
            if val and isinstance(val, str):
                try:
                    data[dt_field] = datetime.fromisoformat(
                        val.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    data[dt_field] = val

        return cls(
            id=data.get("id") or data.get("task_id", ""),
            task_id=data.get("task_id") or data.get("id", ""),
            name=data.get("name", ""),
            status=status,
            progress=data.get("progress", 0),
            total_items=data.get("total_items", 0),
            completed_items=data.get("completed_items", 0),
            failed_items=data.get("failed_items", 0),
            message=data.get("message"),
            error_message=data.get("error_message"),
            output=data.get("output"),
            api_slug=data.get("api_slug"),
            priority=data.get("priority"),
            prediction_id=data.get("prediction_id"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            logs=logs,
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            expires_at=data.get("expires_at"),
        )


@dataclass
class TaskListResponse:
    """Paginated task list."""

    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def from_dict(cls, data: dict) -> "TaskListResponse":
        items_raw = data.get("items", [])
        pagination = data.get("pagination", {})
        items = [TaskResponse.from_dict(item) for item in items_raw]
        return cls(
            items=items,
            total=pagination.get("total", 0),
            page=pagination.get("page", 1),
            page_size=pagination.get("page_size", 20),
            total_pages=pagination.get("total_pages", 0),
        )


@dataclass
class APIResponse:
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    documentation: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None
    status: str = "published"
    is_official: bool = False
    api_type: Optional[str] = None
    handler_name: Optional[str] = None
    upstream_platform_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    config_json: Optional[Dict[str, Any]] = None
    show_detail: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "APIResponse":
        for dt_field in ("created_at", "updated_at"):
            val = data.get(dt_field)
            if val and isinstance(val, str):
                try:
                    data[dt_field] = datetime.fromisoformat(val.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            description=data.get("description"),
            category_id=data.get("category_id"),
            endpoint=data.get("endpoint"),
            method=data.get("method"),
            documentation=data.get("documentation"),
            pricing=data.get("pricing"),
            status=data.get("status", "published"),
            is_official=data.get("is_official", False),
            api_type=data.get("api_type"),
            handler_name=data.get("handler_name"),
            upstream_platform_id=data.get("upstream_platform_id"),
            parameters=data.get("parameters"),
            tags=data.get("tags", []),
            config_json=data.get("config_json"),
            show_detail=data.get("show_detail", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class CategoryResponse:
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    sort_order: int = 0
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CategoryResponse":
        val = data.get("created_at")
        if val and isinstance(val, str):
            try:
                data["created_at"] = datetime.fromisoformat(val.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        return cls(
            id=int(data.get("id", 0)),
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            description=data.get("description"),
            icon_url=data.get("icon_url"),
            sort_order=data.get("sort_order", 0),
            created_at=data.get("created_at"),
        )


@dataclass
class APIListData:
    items: List[APIResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def from_dict(cls, data: dict) -> "APIListData":
        items_raw = data.get("items", [])
        pagination = data.get("pagination", {})
        items = [APIResponse.from_dict(item) for item in items_raw]
        return cls(
            items=items,
            total=pagination.get("total", 0),
            page=pagination.get("page", 1),
            page_size=pagination.get("page_size", 20),
            total_pages=pagination.get("total_pages", 0),
        )
