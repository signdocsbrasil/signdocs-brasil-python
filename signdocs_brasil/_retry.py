"""Retry logic with exponential backoff and jitter.

Retries on HTTP 429, 500, and 503 responses, respecting the Retry-After
header when present. Enforces a maximum total duration of 60 seconds.
"""

from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

import requests

from .errors import TimeoutError

T = TypeVar("T")

_RETRYABLE_STATUS_CODES = {429, 500, 503}
_MAX_TOTAL_DURATION_SECONDS = 60.0
_MAX_DELAY_SECONDS = 30.0


def is_retryable_status(status_code: int) -> bool:
    """Check whether a status code should trigger a retry."""
    return status_code in _RETRYABLE_STATUS_CODES


def calculate_delay(attempt: int, retry_after: int | None = None) -> float:
    """Calculate the delay before the next retry attempt.

    Args:
        attempt: Zero-based attempt index.
        retry_after: Value from the Retry-After header (seconds), if present.

    Returns:
        Delay in seconds.
    """
    if retry_after is not None:
        return float(retry_after)

    # Exponential backoff: 2^attempt seconds + up to 1s jitter
    base_delay = (2 ** attempt) + random.random()
    return float(min(base_delay, _MAX_DELAY_SECONDS))


def with_retry(
    max_retries: int,
    make_request: Callable[[], requests.Response],
) -> requests.Response:
    """Execute an HTTP request with retry logic.

    Args:
        max_retries: Maximum number of retry attempts.
        make_request: A callable that performs the HTTP request and returns a Response.

    Returns:
        The final HTTP Response (either successful or the last retryable response
        after exhausting retries).

    Raises:
        TimeoutError: If the total retry duration exceeds 60 seconds or max retries exhausted
                      (only if no response is available).
    """
    start_time = time.monotonic()

    for attempt in range(max_retries + 1):
        elapsed = time.monotonic() - start_time
        if elapsed > _MAX_TOTAL_DURATION_SECONDS:
            raise TimeoutError("Request exceeded maximum retry duration of 60s")

        response = make_request()

        if not is_retryable_status(response.status_code):
            return response

        # Last attempt: return the response for the caller to parse into an error
        if attempt == max_retries:
            return response

        retry_after_header = response.headers.get("Retry-After")
        retry_after: int | None = None
        if retry_after_header:
            try:
                retry_after = int(retry_after_header)
            except (ValueError, TypeError):
                pass

        delay = calculate_delay(attempt, retry_after)
        time.sleep(delay)

    # Should not be reached, but safeguard
    raise TimeoutError("Max retries exceeded")
