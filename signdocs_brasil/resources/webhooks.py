"""Webhooks resource for managing webhook registrations."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from ..models.webhook import (
    RegisterWebhookRequest,
    RegisterWebhookResponse,
    Webhook,
    WebhookTestResponse,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class WebhooksResource:
    """Webhook registration and management operations."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def register(
        self, request: RegisterWebhookRequest, *, timeout: int | None = None,
    ) -> RegisterWebhookResponse:
        """Register a new webhook endpoint.

        Note: POST /v1/webhooks returns 201 Created.

        Args:
            request: Webhook URL and event types.
            timeout: Per-request timeout in milliseconds.

        Returns:
            RegisterWebhookResponse including the webhook secret.
        """
        data = self._http.request(
            "POST",
            "/v1/webhooks",
            body=request.to_dict(),
            timeout=timeout,
        )
        return RegisterWebhookResponse.from_dict(data)

    def list(self, *, timeout: int | None = None) -> builtins.list[Webhook]:
        """List all registered webhooks.

        Args:
            timeout: Per-request timeout in milliseconds.

        Returns:
            List of Webhook objects.
        """
        data = self._http.request("GET", "/v1/webhooks", timeout=timeout)
        # API returns {"webhooks": [...], "count": N}; accept a bare list
        # defensively for test fixtures that don't wrap.
        items = data.get("webhooks", []) if isinstance(data, dict) else (data or [])
        return [Webhook.from_dict(w) for w in items]

    def delete(self, webhook_id: str, *, timeout: int | None = None) -> None:
        """Delete a webhook registration.

        Note: DELETE /v1/webhooks/{id} returns 204 No Content.

        Args:
            webhook_id: The webhook identifier.
            timeout: Per-request timeout in milliseconds.
        """
        self._http.request("DELETE", f"/v1/webhooks/{webhook_id}", timeout=timeout)

    def test(self, webhook_id: str, *, timeout: int | None = None) -> WebhookTestResponse:
        """Send a test delivery to a webhook endpoint.

        Args:
            webhook_id: The webhook identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            WebhookTestResponse with delivery status.
        """
        data = self._http.request(
            "POST",
            f"/v1/webhooks/{webhook_id}/test",
            timeout=timeout,
        )
        return WebhookTestResponse.from_dict(data)
