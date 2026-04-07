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
    "STEP.STARTED",
    "STEP.COMPLETED",
    "STEP.FAILED",
    "QUOTA.WARNING",
    "API.DEPRECATION_NOTICE",
]


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
class WebhookTestResponse:
    """Response from testing a webhook delivery."""

    delivery_id: str
    status: str
    status_code: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebhookTestResponse:
        return cls(
            delivery_id=data["deliveryId"],
            status=data["status"],
            status_code=data.get("statusCode"),
        )
