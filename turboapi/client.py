from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from turboapi.errors import (
    TurboAPIError,
    NetworkError,
    TimeoutError,
)
from turboapi.models import (
    APIListData,
    APIResponse,
    CategoryResponse,
    TaskListResponse,
    TaskResponse,
    TaskStatus,
)

DEFAULT_BASE_URL = "https://api.turboapi.ai/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_POLL_TIMEOUT = 300.0


class _CallModule:
    """Task creation and management."""

    def __init__(self, client: "TurboAPIClient"):
        self._client = client

    def create(
        self,
        slug_id: str,
        input: Dict[str, Any],
        *,
        prefer_wait: bool = False,
    ) -> TaskResponse:
        """Submit a task for execution.

        Args:
            slug_id: The API slug identifier (e.g. 'karaoke-maker').
            input: Input parameters for the API.
            prefer_wait: If True, server will attempt synchronous execution.

        Returns:
            A TaskResponse with task_id and initial status.
        """
        body: Dict[str, Any] = {"slug_id": slug_id, "input": input}
        headers = {}
        if prefer_wait:
            headers["Prefer-Wait"] = "wait"

        data = self._client._request("POST", "/call", json=body, headers=headers)
        return TaskResponse.from_dict(data)

    def get(self, task_id: str) -> TaskResponse:
        """Get the current status and details of a task.

        Args:
            task_id: The task ID returned from create().

        Returns:
            Current TaskResponse with status and optional output.
        """
        data = self._client._request("GET", f"/call/{task_id}")
        return TaskResponse.from_dict(data)

    def cancel(self, task_id: str) -> None:
        """Request cancellation of a queued task.

        Args:
            task_id: The task ID to cancel.

        Raises:
            NotFoundError: If the task doesn't exist.
            TaskError: If the task cannot be cancelled (already running/complete).
        """
        self._client._request("POST", f"/call/{task_id}/cancel")

    def create_and_wait(
        self,
        slug_id: str,
        input: Dict[str, Any],
        *,
        timeout: float = DEFAULT_POLL_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> TaskResponse:
        """Submit a task and block until it completes or fails.

        This is a convenience method that:
        1. Creates the task via create()
        2. Polls get() until status is terminal
        3. Returns the final result

        Args:
            slug_id: The API slug identifier.
            input: Input parameters for the API.
            timeout: Maximum total wait time in seconds.
            poll_interval: Seconds between status checks.

        Returns:
            Final TaskResponse with output on success.

        Raises:
            TimeoutError: If the task doesn't complete within timeout.
        """
        task = self.create(slug_id, input)

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            task = self.get(task.task_id)

            if task.status and task.status.is_terminal:
                return task

            remaining = deadline - time.monotonic()
            sleep = min(poll_interval, remaining)
            if sleep <= 0:
                break
            time.sleep(sleep)

        raise TimeoutError(
            f"Task {task.task_id} did not complete within {timeout}s",
            error_code="TIMEOUT",
            details={
                "task_id": task.task_id,
                "last_status": task.status.value if task.status else "unknown",
            },
        )


class _TasksModule:
    """Task listing and querying for the authenticated user."""

    def __init__(self, client: "TurboAPIClient"):
        self._client = client

    def list(
        self,
        *,
        status: Optional[TaskStatus] = None,
        api_slug: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TaskListResponse:
        """List tasks for the authenticated user.

        Args:
            status: Filter by task status.
            api_slug: Filter by API slug.
            page: Page number (1-indexed).
            page_size: Items per page (max 100).

        Returns:
            A paginated list of TaskResponse items.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status.value
        if api_slug:
            params["api_slug"] = api_slug

        data = self._client._request("GET", "/tasks", params=params)
        return TaskListResponse.from_dict(data)

    def get(self, task_id: str) -> TaskResponse:
        """Get a specific task's detail.

        Args:
            task_id: The task ID.

        Returns:
            Full TaskResponse for the given task.
        """
        data = self._client._request("GET", f"/tasks/{task_id}")
        return TaskResponse.from_dict(data)

    def logs(
        self,
        task_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Get execution logs for a task.

        Args:
            task_id: The task ID.
            page: Page number (1-indexed).
            page_size: Items per page (max 100).

        Returns:
            Raw response data containing log items.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        return self._client._request("GET", f"/tasks/{task_id}/logs", params=params)


class _ApisModule:
    """API Market listing and discovery."""

    def __init__(self, client: "TurboAPIClient"):
        self._client = client

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> APIListData:
        """List available APIs in the marketplace.

        Args:
            page: Page number (1-indexed).
            page_size: Items per page (max 100).
            category: Filter by category slug.
            tags: Filter by tag names.
            search: Search in name and description.
            sort_by: Sort field ('created_at', 'name', 'popularity').
            sort_order: Sort order ('asc' or 'desc').

        Returns:
            A paginated list of APIResponse items.
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if category:
            params["category"] = category
        if tags:
            params["tags"] = ",".join(tags)
        if search:
            params["search"] = search

        data = self._client._request("GET", "/apis", params=params)
        return APIListData.from_dict(data)

    def get(self, slug: str) -> APIResponse:
        """Get details of a specific API by its slug.

        Args:
            slug: The API slug identifier (e.g. 'karaoke-maker').

        Returns:
            Full APIResponse with parameters and documentation.
        """
        data = self._client._request("GET", f"/apis/{slug}")
        return APIResponse.from_dict(data)

    def categories(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List API categories.

        Args:
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Raw response data containing category items.
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        return self._client._request("GET", "/apis/categories", params=params)


class TurboAPIClient:
    """TurboAPI client for calling AI services.

    The client is configured once and provides access to the Call and Tasks APIs
    via the `.call` and `.tasks` attributes.

    Authentication is handled via an API key, passed as a Bearer token.

    Usage:
        client = TurboAPIClient(api_key="tbp_xxxxx")

        # Quick call with blocking wait
        result = client.call.create_and_wait("karaoke-maker", {
            "audio_file": "https://...",
            "task_key": "demo-001",
        })
        print(result.output)

        # Or manual two-step
        task = client.call.create("some-api", {"key": "value"})
        status = client.call.get(task.task_id)
        client.call.cancel(task.task_id)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

        self.apis = _ApisModule(self)
        self.call = _CallModule(self)
        self.tasks = _TasksModule(self)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an HTTP request to the TurboAPI backend.

        Args:
            method: HTTP method.
            path: URL path (appended to base_url).
            json: JSON body.
            params: Query parameters.
            headers: Additional request headers.

        Returns:
            The 'data' field from the API response on success.

        Raises:
            TurboAPIError subclasses on failure.
        """
        url = f"{self.base_url}{path}"
        req_headers = {**self._headers, **(headers or {})}

        try:
            with httpx.Client(timeout=self.timeout) as http:
                response = http.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    headers=req_headers,
                )
        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"Request timed out after {self.timeout}s",
                error_code="TIMEOUT_ERROR",
            ) from e
        except httpx.TransportError as e:
            raise NetworkError(
                f"Network error: {e}",
                error_code="NETWORK_ERROR",
            ) from e

        body = response.json()

        if not body.get("success", False):
            raise TurboAPIError.from_response(response.status_code, body)

        return body.get("data")
