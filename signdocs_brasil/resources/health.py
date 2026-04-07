"""Health check resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.health import HealthCheckResponse, HealthHistoryResponse

if TYPE_CHECKING:
    from .._http_client import HttpClient


class HealthResource:
    """API health check operations.

    Health endpoints do not require authentication.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def check(self, *, timeout: int | None = None) -> HealthCheckResponse:
        """Check current API health status.

        Args:
            timeout: Per-request timeout in milliseconds.

        Returns:
            HealthCheckResponse with status, version, and service details.
        """
        data = self._http.request("GET", "/health", no_auth=True, timeout=timeout)
        return HealthCheckResponse.from_dict(data)

    def history(self, *, timeout: int | None = None) -> HealthHistoryResponse:
        """Get historical health check entries.

        Args:
            timeout: Per-request timeout in milliseconds.

        Returns:
            HealthHistoryResponse with a list of past health check entries.
        """
        data = self._http.request("GET", "/health/history", no_auth=True, timeout=timeout)
        return HealthHistoryResponse.from_dict(data)
