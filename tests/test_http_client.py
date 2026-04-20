"""Tests for the internal HTTP client."""

from unittest.mock import MagicMock

import pytest
import responses

from signdocs_brasil._auth import AuthHandler
from signdocs_brasil._http_client import HttpClient
from signdocs_brasil.errors import (
    BadRequestError,
    NotFoundError,
    RateLimitError,
)

BASE_URL = "https://api.signdocs.com.br"


def make_client(max_retries=0):
    auth = MagicMock(spec=AuthHandler)
    auth.get_access_token.return_value = "test-token"
    client = HttpClient(
        base_url=BASE_URL,
        timeout=30000,
        max_retries=max_retries,
        auth=auth,
    )
    return client, auth


class TestHttpClient:
    @responses.activate
    def test_authorization_header(self):
        responses.get(f"{BASE_URL}/v1/test", json={"ok": True}, status=200)

        client, auth = make_client()
        client.request("GET", "/v1/test")

        req = responses.calls[0].request
        assert req.headers["Authorization"] == "Bearer test-token"

    @responses.activate
    def test_user_agent_header(self):
        responses.get(f"{BASE_URL}/v1/test", json={"ok": True}, status=200)

        client, _ = make_client()
        client.request("GET", "/v1/test")

        req = responses.calls[0].request
        assert "signdocs-brasil-python/1.3.0" in req.headers["User-Agent"]

    @responses.activate
    def test_no_auth_skips_authorization(self):
        responses.get(f"{BASE_URL}/health", json={"status": "ok"}, status=200)

        client, auth = make_client()
        client.request("GET", "/health", no_auth=True)

        assert "Authorization" not in responses.calls[0].request.headers
        auth.get_access_token.assert_not_called()

    @responses.activate
    def test_json_body(self):
        responses.post(f"{BASE_URL}/v1/transactions", json={"id": "tx_1"}, status=200)

        client, _ = make_client()
        result = client.request("POST", "/v1/transactions", body={"name": "test"})

        assert result["id"] == "tx_1"
        req = responses.calls[0].request
        assert "application/json" in req.headers.get("Content-Type", "")

    @responses.activate
    def test_query_params(self):
        responses.get(f"{BASE_URL}/v1/transactions", json={"items": []}, status=200)

        client, _ = make_client()
        client.request("GET", "/v1/transactions", query={"status": "active", "limit": 10})

        assert "status=active" in responses.calls[0].request.url
        assert "limit=10" in responses.calls[0].request.url

    @responses.activate
    def test_omits_none_query_params(self):
        responses.get(f"{BASE_URL}/v1/transactions", json={"items": []}, status=200)

        client, _ = make_client()
        client.request("GET", "/v1/transactions", query={"status": "active", "next_token": None})

        assert "next_token" not in responses.calls[0].request.url

    @responses.activate
    def test_204_returns_none(self):
        responses.delete(f"{BASE_URL}/v1/webhooks/123", status=204)

        client, _ = make_client()
        result = client.request("DELETE", "/v1/webhooks/123")

        assert result is None

    @responses.activate
    def test_400_raises_bad_request(self):
        responses.post(
            f"{BASE_URL}/v1/test",
            json={"type": "about:blank", "title": "Bad Request", "status": 400},
            status=400,
        )

        client, _ = make_client()
        with pytest.raises(BadRequestError):
            client.request("POST", "/v1/test")

    @responses.activate
    def test_404_raises_not_found(self):
        responses.get(
            f"{BASE_URL}/v1/transactions/missing",
            json={"type": "about:blank", "title": "Not Found", "status": 404},
            status=404,
        )

        client, _ = make_client()
        with pytest.raises(NotFoundError):
            client.request("GET", "/v1/transactions/missing")

    @responses.activate
    def test_429_raises_rate_limit_with_retry_after(self):
        responses.get(
            f"{BASE_URL}/v1/test",
            json={"type": "about:blank", "title": "Rate Limited", "status": 429},
            status=429,
            headers={"Retry-After": "5"},
        )

        client, _ = make_client()
        with pytest.raises(RateLimitError) as exc_info:
            client.request("GET", "/v1/test")
        assert exc_info.value.retry_after_seconds == 5

    @responses.activate
    def test_idempotency_key_explicit(self):
        responses.post(f"{BASE_URL}/v1/transactions", json={"id": "tx_1"}, status=200)

        client, _ = make_client()
        client.request_with_idempotency(
            "POST", "/v1/transactions", body={"name": "test"}, idempotency_key="my-key",
        )

        assert responses.calls[0].request.headers["X-Idempotency-Key"] == "my-key"

    @responses.activate
    def test_idempotency_key_auto_generated(self):
        responses.post(f"{BASE_URL}/v1/transactions", json={"id": "tx_1"}, status=200)

        client, _ = make_client()
        client.request_with_idempotency("POST", "/v1/transactions", body={"name": "test"})

        key = responses.calls[0].request.headers.get("X-Idempotency-Key")
        assert key is not None
        assert len(key) > 0
