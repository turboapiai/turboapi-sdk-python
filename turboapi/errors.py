"""
Exception hierarchy for the TurboAPI SDK.

Maps backend error codes to typed Python exceptions.
"""

from typing import Any, Dict, Optional


class TurboAPIError(Exception):
    """Base exception for all TurboAPI SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code or "UNKNOWN"
        self.details = details
        self.request_id = request_id
        super().__init__(message)

    @property
    def message(self) -> str:
        return str(self.args[0]) if self.args else ""

    @classmethod
    def from_response(
        cls,
        status_code: int,
        body: dict,
    ) -> "TurboAPIError":
        """Create an appropriate error from an API error response."""
        error = body.get("error", {})
        error_code = error.get("code", "UNKNOWN")
        message = error.get("message", "Unknown error")
        details = error.get("details")
        meta = body.get("meta", {})
        request_id = meta.get("request_id")

        # Map error codes to typed exceptions
        error_class = _ERROR_CODE_MAP.get(error_code, TurboAPIError)

        return error_class(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details=details,
            request_id=request_id,
        )


class AuthenticationError(TurboAPIError):
    """Invalid or missing API key / authentication."""


class RateLimitError(TurboAPIError):
    """Rate limit exceeded."""

    @property
    def retry_after(self) -> Optional[int]:
        """Get the retry-after duration in seconds, if provided."""
        if self.details and "retry_after" in self.details:
            return int(self.details["retry_after"])
        return None


class NotFoundError(TurboAPIError):
    """Resource not found."""


class ValidationError(TurboAPIError):
    """Request validation failed."""


class TaskError(TurboAPIError):
    """Task execution failed."""


class ServerError(TurboAPIError):
    """Backend server error (5xx)."""


class NetworkError(TurboAPIError):
    """Network/connection error."""


class TimeoutError(TurboAPIError):
    """Request or task timeout."""


# Map backend error code prefixes to exception classes
_ERROR_CODE_MAP: Dict[str, type[TurboAPIError]] = {
    # Auth errors
    "AUTH_": AuthenticationError,
    "UNAUTHORIZED": AuthenticationError,
    "AUTH_TOKEN_EXPIRED": AuthenticationError,
    "AUTH_INVALID_TOKEN": AuthenticationError,
    # General errors
    "NOT_FOUND": NotFoundError,
    "API_NOT_FOUND": NotFoundError,
    "USER_NOT_FOUND": NotFoundError,
    "RATE_LIMITED": RateLimitError,
    "RATE_LIMIT": RateLimitError,
    "VALIDATION_ERROR": ValidationError,
    "VALIDATION_": ValidationError,
    "BAD_REQUEST": ValidationError,
    "FORBIDDEN": AuthenticationError,
    "CALL_": TaskError,
    "CALL_FAILED": ServerError,
    "INTERNAL_ERROR": ServerError,
    "INTERNAL_": ServerError,
    "POINTS_INSUFFICIENT": TaskError,
}
