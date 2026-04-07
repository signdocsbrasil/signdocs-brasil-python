"""Internal HTTP client wrapping requests with auth, retry, and error handling."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

import requests as _requests

from ._auth import AuthHandler
from ._retry import with_retry
from .errors import (
    ConnectionError,
    TimeoutError,
    parse_api_error,
)

_SDK_VERSION = "1.0.0"
_USER_AGENT = f"signdocs-brasil-python/{_SDK_VERSION}"


class HttpClient:
    """Low-level HTTP client used by all resource classes.

    Handles authentication, retry logic, JSON serialization/deserialization,
    and error mapping.

    Args:
        base_url: API base URL.
        timeout: Request timeout in milliseconds.
        max_retries: Maximum retry count for retryable status codes.
        auth: AuthHandler instance for Bearer token management.
        session: Optional custom ``requests.Session`` to use for HTTP calls.
        logger: Optional ``logging.Logger`` for request/response logging.
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout: int,
        max_retries: int,
        auth: AuthHandler,
        session: _requests.Session | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout / 1000.0
        self._max_retries = max_retries
        self._auth = auth
        self._session = session if session is not None else _requests.Session()
        self._session.headers["User-Agent"] = _USER_AGENT
        self._logger = logger

    def request(
        self,
        method: str,
        path: str,
        *,
        body: Any | None = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        no_auth: bool = False,
        timeout: int | None = None,
    ) -> Any:
        """Perform an HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: URL path relative to the base URL.
            body: Request body (will be JSON-serialized).
            query: Query parameters. Values of None are omitted.
            headers: Additional request headers.
            no_auth: If True, skip the Authorization header.
            timeout: Per-request timeout in milliseconds. Overrides the default
                client timeout when provided.

        Returns:
            Parsed JSON response body, or None for 204 No Content.

        Raises:
            SignDocsBrasilApiError: On non-2xx API responses.
            ConnectionError: On network failures.
            TimeoutError: On request or retry timeouts.
        """
        url = self._build_url(path)
        effective_timeout = (timeout / 1000.0) if timeout is not None else self._timeout_seconds

        # Filter out None values from query params
        cleaned_query: dict[str, str] | None = None
        if query:
            cleaned_query = {
                k: str(v) for k, v in query.items() if v is not None
            }
            if not cleaned_query:
                cleaned_query = None

        def make_request() -> _requests.Response:
            req_headers: dict[str, str] = {}
            if headers:
                req_headers.update(headers)

            if not no_auth:
                token = self._auth.get_access_token()
                req_headers["Authorization"] = f"Bearer {token}"

            kwargs: dict[str, Any] = {
                "method": method,
                "url": url,
                "headers": req_headers,
                "params": cleaned_query,
                "timeout": effective_timeout,
            }

            if body is not None:
                req_headers["Content-Type"] = "application/json"
                kwargs["json"] = body

            try:
                return self._session.request(**kwargs)
            except _requests.exceptions.Timeout as exc:
                raise TimeoutError(
                    f"Request to {path} timed out after {effective_timeout * 1000:.0f}ms"
                ) from exc
            except _requests.exceptions.ConnectionError as exc:
                raise ConnectionError(f"Failed to connect to {url}: {exc}") from exc
            except _requests.RequestException as exc:
                raise ConnectionError(f"Request to {url} failed: {exc}") from exc

        start = time.monotonic()
        response = with_retry(self._max_retries, make_request)
        duration_ms = int((time.monotonic() - start) * 1000)

        if self._logger is not None:
            if response.ok:
                self._logger.info(
                    "request completed method=%s path=%s status=%d duration_ms=%d",
                    method,
                    path,
                    response.status_code,
                    duration_ms,
                )
            else:
                self._logger.warning(
                    "request failed method=%s path=%s status=%d duration_ms=%d",
                    method,
                    path,
                    response.status_code,
                    duration_ms,
                )

        return self._parse_response(response, path)

    def request_with_idempotency(
        self,
        method: str,
        path: str,
        *,
        body: Any | None = None,
        idempotency_key: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> Any:
        """Perform a request with an idempotency key header.

        If no key is provided, a UUID4 is generated automatically.

        Args:
            method: HTTP method.
            path: URL path.
            body: Request body.
            idempotency_key: Optional explicit idempotency key.
            headers: Additional request headers.
            timeout: Per-request timeout in milliseconds.

        Returns:
            Parsed JSON response body.
        """
        key = idempotency_key or str(uuid.uuid4())
        merged_headers = dict(headers or {})
        merged_headers["X-Idempotency-Key"] = key
        return self.request(method, path, body=body, headers=merged_headers, timeout=timeout)

    def _build_url(self, path: str) -> str:
        """Construct a full URL from the base URL and path."""
        if path.startswith("/"):
            return f"{self._base_url}{path}"
        return f"{self._base_url}/{path}"

    @staticmethod
    def _parse_response(response: _requests.Response, path: str) -> Any:
        """Parse a response, raising SDK errors for non-2xx status codes.

        Args:
            response: The HTTP response.
            path: The request path (for error messages).

        Returns:
            Parsed JSON body or None for 204 responses.

        Raises:
            SignDocsBrasilApiError: For non-2xx responses.
        """
        if response.status_code == 204:
            return None

        content_type = response.headers.get("Content-Type", "")
        body: Any
        if "application/json" in content_type or "application/problem+json" in content_type:
            try:
                body = response.json()
            except ValueError:
                body = response.text
        else:
            body = response.text

        if not response.ok:
            retry_after_header = response.headers.get("Retry-After")
            retry_after: int | None = None
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                except (ValueError, TypeError):
                    pass
            raise parse_api_error(response.status_code, body, retry_after)

        return body
