import httpx
import pytest
from pytest_httpx import HTTPXMock

from turboapi import TurboAPIClient, TaskStatus, APIResponse
from turboapi.errors import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
)


@pytest.fixture
def client() -> TurboAPIClient:
    return TurboAPIClient(api_key="test-key", base_url="https://test.turboapi.ai/api/v1")


def test_call_create(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url="https://test.turboapi.ai/api/v1/call",
        json={
            "success": True,
            "data": {
                "id": "task-001",
                "task_id": "task-001",
                "name": "karaoke-maker",
                "status": "queued",
                "progress": 0,
            },
        },
    )

    task = client.call.create("karaoke-maker", {"audio_file": "https://example.com/a.mp3"})

    assert task.task_id == "task-001"
    assert task.status == TaskStatus.QUEUED
    assert task.name == "karaoke-maker"


def test_call_get(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/call/task-001",
        json={
            "success": True,
            "data": {
                "id": "task-001",
                "task_id": "task-001",
                "name": "karaoke-maker",
                "status": "succeeded",
                "progress": 100,
                "output": {"video_url": "https://example.com/result.mp4"},
            },
        },
    )

    task = client.call.get("task-001")

    assert task.status == TaskStatus.SUCCEEDED
    assert task.output == {"video_url": "https://example.com/result.mp4"}


def test_call_cancel(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url="https://test.turboapi.ai/api/v1/call/task-001/cancel",
        json={
            "success": True,
            "data": {"message": "Task cancelled"},
        },
    )

    client.call.cancel("task-001")


def test_tasks_list(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/tasks?page=1&page_size=20",
        json={
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "task-001",
                        "task_id": "task-001",
                        "name": "karaoke-maker",
                        "status": "succeeded",
                    },
                    {
                        "id": "task-002",
                        "task_id": "task-002",
                        "name": "minimax-music",
                        "status": "processing",
                    },
                ],
                "pagination": {
                    "total": 2,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 1,
                },
            },
        },
    )

    result = client.tasks.list()

    assert len(result.items) == 2
    assert result.total == 2


def test_tasks_get(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/tasks/task-001",
        json={
            "success": True,
            "data": {
                "id": "task-001",
                "task_id": "task-001",
                "name": "karaoke-maker",
                "status": "succeeded",
                "output": {"video_url": "https://example.com/r.mp4"},
            },
        },
    )

    task = client.tasks.get("task-001")

    assert task.status == TaskStatus.SUCCEEDED


def test_tasks_logs(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/tasks/task-001/logs?page=1&page_size=50",
        json={
            "success": True,
            "data": {
                "items": [
                    {
                        "timestamp": "2026-01-01T00:00:00Z",
                        "level": "info",
                        "message": "Task started",
                    }
                ],
                "pagination": {"total": 1, "page": 1, "page_size": 50, "total_pages": 1},
            },
        },
    )

    result = client.tasks.logs("task-001")

    assert "items" in result


def test_authentication_error(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/tasks?page=1&page_size=20",
        status_code=401,
        json={
            "success": False,
            "error": {"code": "UNAUTHORIZED", "message": "Invalid API key"},
            "meta": {"request_id": "abc123", "timestamp": "2026-01-01T00:00:00Z"},
        },
    )

    with pytest.raises(AuthenticationError) as exc:
        client.tasks.list()
    assert "Invalid API key" in str(exc.value)


def test_not_found_error(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/call/non-existent",
        status_code=404,
        json={
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Task not found"},
            "meta": {"request_id": "abc", "timestamp": "2026-01-01T00:00:00Z"},
        },
    )

    with pytest.raises(NotFoundError):
        client.call.get("non-existent")


def test_rate_limit_error(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url="https://test.turboapi.ai/api/v1/call",
        status_code=429,
        json={
            "success": False,
            "error": {
                "code": "RATE_LIMITED",
                "message": "Rate limit exceeded",
                "details": {"retry_after": 30},
            },
            "meta": {"request_id": "def", "timestamp": "2026-01-01T00:00:00Z"},
        },
    )

    with pytest.raises(RateLimitError) as exc:
        client.call.create("test", {"k": "v"})
    assert exc.value.retry_after == 30


def test_apis_list(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/apis?page=1&page_size=20&sort_by=created_at&sort_order=desc",
        json={
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "1",
                        "name": "Karaoke Maker",
                        "slug": "karaoke-maker",
                        "status": "published",
                        "tags": ["audio", "video"],
                    },
                    {
                        "id": "2",
                        "name": "Minimax Music",
                        "slug": "minimax-music-2.6",
                        "status": "published",
                        "tags": ["music"],
                    },
                ],
                "pagination": {
                    "total": 2,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 1,
                },
            },
        },
    )

    result = client.apis.list()

    assert len(result.items) == 2
    assert result.items[0].slug == "karaoke-maker"
    assert result.items[1].name == "Minimax Music"
    assert result.total == 2


def test_apis_get(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/apis/karaoke-maker",
        json={
            "success": True,
            "data": {
                "id": "1",
                "name": "Karaoke Maker",
                "slug": "karaoke-maker",
                "description": "Generate karaoke videos",
                "status": "published",
                "parameters": {
                    "input": {
                        "type": "object",
                        "properties": {
                            "audio_file": {"type": "string", "format": "uri"}
                        },
                        "required": ["audio_file"],
                    }
                },
                "tags": ["audio", "video"],
            },
        },
    )

    api = client.apis.get("karaoke-maker")

    assert isinstance(api, APIResponse)
    assert api.slug == "karaoke-maker"
    assert api.description == "Generate karaoke videos"
    assert "audio_file" in api.parameters["input"]["required"]


def test_apis_list_with_filters(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/apis?page=1&page_size=10&category=ai&search=video&sort_by=name&sort_order=asc",
        json={
            "success": True,
            "data": {
                "items": [
                    {
                        "id": "1",
                        "name": "Karaoke Maker",
                        "slug": "karaoke-maker",
                        "status": "published",
                    }
                ],
                "pagination": {"total": 1, "page": 1, "page_size": 10, "total_pages": 1},
            },
        },
    )

    result = client.apis.list(
        page=1,
        page_size=10,
        category="ai",
        search="video",
        sort_by="name",
        sort_order="asc",
    )

    assert len(result.items) == 1
    assert result.items[0].slug == "karaoke-maker"


def test_create_and_wait(client: TurboAPIClient, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url="https://test.turboapi.ai/api/v1/call",
        json={
            "success": True,
            "data": {
                "id": "task-wait-001",
                "task_id": "task-wait-001",
                "name": "test-api",
                "status": "queued",
            },
        },
    )
    httpx_mock.add_response(
        method="GET",
        url="https://test.turboapi.ai/api/v1/call/task-wait-001",
        json={
            "success": True,
            "data": {
                "id": "task-wait-001",
                "task_id": "task-wait-001",
                "name": "test-api",
                "status": "succeeded",
                "output": {"result": "done"},
            },
        },
    )

    task = client.call.create_and_wait("test-api", {"k": "v"}, timeout=10, poll_interval=0.1)

    assert task.status == TaskStatus.SUCCEEDED
    assert task.output == {"result": "done"}
