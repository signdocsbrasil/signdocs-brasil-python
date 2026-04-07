"""Health check data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class ServiceHealth:
    """Health status of an individual service dependency."""

    status: str
    latency: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceHealth:
        return cls(
            status=data["status"],
            latency=data.get("latency"),
        )


@dataclass
class HealthCheckResponse:
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: str
    services: dict[str, ServiceHealth] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HealthCheckResponse:
        services = None
        if data.get("services"):
            services = {
                name: ServiceHealth.from_dict(svc)
                for name, svc in data["services"].items()
            }
        return cls(
            status=data["status"],
            version=data["version"],
            timestamp=data["timestamp"],
            services=services,
        )


@dataclass
class HealthHistoryResponse:
    """Historical health check entries."""

    entries: list[HealthCheckResponse] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HealthHistoryResponse:
        return cls(
            entries=[HealthCheckResponse.from_dict(e) for e in data.get("entries", [])],
        )
