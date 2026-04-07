"""Error hierarchy for SignDocs Brasil SDK.

Mirrors the TypeScript SDK error structure:
    SignDocsBrasilError
        SignDocsBrasilApiError
            BadRequestError (400)
            UnauthorizedError (401)
            ForbiddenError (403)
            NotFoundError (404)
            ConflictError (409)
            UnprocessableEntityError (422)
            RateLimitError (429)
            InternalServerError (500)
            ServiceUnavailableError (503)
        AuthenticationError
        ConnectionError
        TimeoutError
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProblemDetail:
    """RFC 7807 Problem Detail representation."""

    type: str
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProblemDetail:
        known_keys = {"type", "title", "status", "detail", "instance"}
        extra = {k: v for k, v in data.items() if k not in known_keys}
        return cls(
            type=data.get("type", ""),
            title=data.get("title", ""),
            status=data.get("status", 0),
            detail=data.get("detail"),
            instance=data.get("instance"),
            extra=extra,
        )


class SignDocsBrasilError(Exception):
    """Base exception for all SignDocs Brasil SDK errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SignDocsBrasilApiError(SignDocsBrasilError):
    """API error with HTTP status and RFC 7807 problem detail."""

    def __init__(self, problem_detail: ProblemDetail) -> None:
        message = problem_detail.detail or problem_detail.title
        super().__init__(message)
        self.status: int = problem_detail.status
        self.type: str = problem_detail.type
        self.title: str = problem_detail.title
        self.detail: str | None = problem_detail.detail
        self.instance: str | None = problem_detail.instance
        self.problem_detail: ProblemDetail = problem_detail


class BadRequestError(SignDocsBrasilApiError):
    """HTTP 400 Bad Request."""

    pass


class UnauthorizedError(SignDocsBrasilApiError):
    """HTTP 401 Unauthorized."""

    pass


class ForbiddenError(SignDocsBrasilApiError):
    """HTTP 403 Forbidden."""

    pass


class NotFoundError(SignDocsBrasilApiError):
    """HTTP 404 Not Found."""

    pass


class ConflictError(SignDocsBrasilApiError):
    """HTTP 409 Conflict."""

    pass


class UnprocessableEntityError(SignDocsBrasilApiError):
    """HTTP 422 Unprocessable Entity."""

    pass


class RateLimitError(SignDocsBrasilApiError):
    """HTTP 429 Too Many Requests."""

    def __init__(
        self, problem_detail: ProblemDetail, retry_after_seconds: int | None = None
    ) -> None:
        super().__init__(problem_detail)
        self.retry_after_seconds: int | None = retry_after_seconds


class InternalServerError(SignDocsBrasilApiError):
    """HTTP 500 Internal Server Error."""

    pass


class ServiceUnavailableError(SignDocsBrasilApiError):
    """HTTP 503 Service Unavailable."""

    pass


class AuthenticationError(SignDocsBrasilError):
    """Authentication/token exchange failure."""

    pass


class ConnectionError(SignDocsBrasilError):
    """Network connectivity failure."""

    pass


class TimeoutError(SignDocsBrasilError):
    """Request or retry timeout."""

    pass


_ERROR_MAP: dict[int, type[SignDocsBrasilApiError]] = {
    400: BadRequestError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
    500: InternalServerError,
    503: ServiceUnavailableError,
}


def parse_api_error(
    status: int, body: Any, retry_after: int | None = None
) -> SignDocsBrasilApiError:
    """Parse an HTTP error response into the appropriate SDK error type.

    Args:
        status: HTTP status code.
        body: Parsed response body (dict or str).
        retry_after: Retry-After header value in seconds, if present.

    Returns:
        The appropriate SignDocsBrasilApiError subclass instance.
    """
    if isinstance(body, dict) and "type" in body:
        problem_detail = ProblemDetail.from_dict(body)
    else:
        problem_detail = ProblemDetail(
            type=f"https://api.signdocs.com.br/errors/{status}",
            title=f"HTTP {status}",
            status=status,
            detail=body if isinstance(body, str) else None,
        )

    if status == 429:
        return RateLimitError(problem_detail, retry_after)

    error_class = _ERROR_MAP.get(status, SignDocsBrasilApiError)
    return error_class(problem_detail)
