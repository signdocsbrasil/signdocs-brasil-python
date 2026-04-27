"""Webhook-related data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

WebhookEventType = Literal[
    "TRANSACTION.CREATED",
    "TRANSACTION.COMPLETED",
    "TRANSACTION.CANCELLED",
    "TRANSACTION.FAILED",
    "TRANSACTION.EXPIRED",
    "TRANSACTION.FALLBACK",
    "TRANSACTION.DEADLINE_APPROACHING",
    "STEP.STARTED",
    "STEP.COMPLETED",
    "STEP.FAILED",
    "STEP.PURPOSE_DISCLOSURE_SENT",
    "QUOTA.WARNING",
    "API.DEPRECATION_NOTICE",
    "SIGNING_SESSION.CREATED",
    "SIGNING_SESSION.COMPLETED",
    "SIGNING_SESSION.CANCELLED",
    "SIGNING_SESSION.EXPIRED",
]

#: Webhook events that are part of the NT65 INSS consignado flow. Events
#: in this set are only emitted for tenants with ``nt65ComplianceEnabled``.
NT65_EVENTS: frozenset[str] = frozenset(
    {
        "TRANSACTION.DEADLINE_APPROACHING",
        "STEP.PURPOSE_DISCLOSURE_SENT",
    }
)


@dataclass
class RegisterWebhookRequest:
    """Request to register a new webhook."""

    url: str
    events: list[WebhookEventType]

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "events": list(self.events),
        }


@dataclass
class RegisterWebhookResponse:
    """Response after registering a webhook (includes the secret)."""

    webhook_id: str
    url: str
    secret: str
    events: list[WebhookEventType]
    status: Literal["ACTIVE"]
    created_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegisterWebhookResponse:
        return cls(
            webhook_id=data["webhookId"],
            url=data["url"],
            secret=data["secret"],
            events=data["events"],
            status=data["status"],
            created_at=data["createdAt"],
        )


@dataclass
class Webhook:
    """A registered webhook."""

    webhook_id: str
    url: str
    events: list[WebhookEventType]
    status: str
    created_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Webhook:
        return cls(
            webhook_id=data["webhookId"],
            url=data["url"],
            events=data["events"],
            status=data["status"],
            created_at=data["createdAt"],
        )


@dataclass
class WebhookPayload:
    """Webhook event payload."""

    id: str
    event_type: WebhookEventType
    tenant_id: str
    timestamp: str
    data: dict[str, Any]
    transaction_id: str | None = None
    test: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebhookPayload:
        return cls(
            id=data["id"],
            event_type=data["eventType"],
            tenant_id=data["tenantId"],
            timestamp=data["timestamp"],
            data=data["data"],
            transaction_id=data.get("transactionId"),
            test=data.get("test"),
        )


@dataclass
class WebhookTestDelivery:
    """Result of a synchronous test delivery to the webhook endpoint."""

    http_status: int
    success: bool
    timestamp: str
    error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebhookTestDelivery:
        return cls(
            http_status=data["httpStatus"],
            success=data["success"],
            timestamp=data["timestamp"],
            error=data.get("error"),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "httpStatus": self.http_status,
            "success": self.success,
            "timestamp": self.timestamp,
        }
        if self.error is not None:
            out["error"] = self.error
        return out


@dataclass
class WebhookTestResponse:
    """Response from POST /v1/webhooks/{id}/test.

    The API returns the webhook identifier alongside the synchronous
    delivery attempt result (HTTP status code, success flag, optional
    error message, and dispatch timestamp).
    """

    webhook_id: str
    test_delivery: WebhookTestDelivery

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebhookTestResponse:
        return cls(
            webhook_id=data["webhookId"],
            test_delivery=WebhookTestDelivery.from_dict(data["testDelivery"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "webhookId": self.webhook_id,
            "testDelivery": self.test_delivery.to_dict(),
        }
