"""Retry integration tests: verify the retry loop works end-to-end."""

import pytest
import responses

from signdocs_brasil._config import ClientConfig
from signdocs_brasil.client import SignDocsBrasilClient
from signdocs_brasil.errors import (
    BadRequestError,
    ServiceUnavailableError,
)

BASE_URL = "https://api.signdocs.com.br"
TOKEN_URL = f"{BASE_URL}/oauth2/token"

TOKEN_RESPONSE = {
    "access_token": "test-token",
    "token_type": "Bearer",
    "expires_in": 900,
    "scope": "transactions:read",
}

SUCCESS_BODY = {
    "tenantId": "abc123",
    "transactionId": "tx-001",
    "status": "CREATED",
    "purpose": "DOCUMENT_SIGNATURE",
    "policy": {"profile": "CLICK_ONLY"},
    "signer": {"name": "Test", "userExternalId": "u1"},
    "steps": [],
    "expiresAt": "2024-12-31T00:00:00Z",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z",
}

ERROR_BODY_503 = {
    "type": "https://api.signdocs.com.br/errors/service-unavailable",
    "title": "Service Unavailable",
    "status": 503,
    "detail": "DynamoDB throughput exceeded",
}

ERROR_BODY_400 = {
    "type": "https://api.signdocs.com.br/errors/bad-request",
    "title": "Bad Request",
    "status": 400,
    "detail": "Invalid input",
}


def create_client(max_retries: int) -> SignDocsBrasilClient:
    return SignDocsBrasilClient(
        ClientConfig(
            client_id="test-client",
            client_secret="test-secret",
            base_url=BASE_URL,
            max_retries=max_retries,
        )
    )


def add_token_mock():
    responses.post(TOKEN_URL, json=TOKEN_RESPONSE, status=200)


class TestRetryIntegration:
    @responses.activate(assert_all_requests_are_fired=True)
    def test_503_then_200_retries_and_succeeds(self):
        add_token_mock()
        responses.get(f"{BASE_URL}/v1/transactions/tx-001", json=ERROR_BODY_503, status=503)
        responses.get(f"{BASE_URL}/v1/transactions/tx-001", json=SUCCESS_BODY, status=200)

        client = create_client(max_retries=3)
        result = client.transactions.get("tx-001")

        assert result.transaction_id == "tx-001"
        # 1 token call + 2 API calls
        assert len(responses.calls) == 3

    @responses.activate(assert_all_requests_are_fired=True)
    def test_429_with_retry_after_then_200(self):
        add_token_mock()
        responses.get(
            f"{BASE_URL}/v1/transactions/tx-001",
            json={"type": "about:blank", "title": "Rate Limited", "status": 429},
            status=429,
            headers={"Retry-After": "1"},
        )
        responses.get(f"{BASE_URL}/v1/transactions/tx-001", json=SUCCESS_BODY, status=200)

        client = create_client(max_retries=3)
        result = client.transactions.get("tx-001")

        assert result.transaction_id == "tx-001"
        assert len(responses.calls) == 3

    @responses.activate(assert_all_requests_are_fired=True)
    def test_503_x3_then_200_four_total_requests(self):
        add_token_mock()
        for _ in range(3):
            responses.get(f"{BASE_URL}/v1/transactions/tx-001", json=ERROR_BODY_503, status=503)
        responses.get(f"{BASE_URL}/v1/transactions/tx-001", json=SUCCESS_BODY, status=200)

        client = create_client(max_retries=3)
        result = client.transactions.get("tx-001")

        assert result.transaction_id == "tx-001"
        # 1 token + 4 API calls
        assert len(responses.calls) == 5

    @responses.activate(assert_all_requests_are_fired=True)
    def test_503_x4_exhausts_retries(self):
        add_token_mock()
        for _ in range(4):
            responses.get(f"{BASE_URL}/v1/transactions/tx-001", json=ERROR_BODY_503, status=503)

        client = create_client(max_retries=3)
        with pytest.raises(ServiceUnavailableError):
            client.transactions.get("tx-001")

        # 1 token + 4 API calls
        assert len(responses.calls) == 5

    @responses.activate(assert_all_requests_are_fired=True)
    def test_non_retryable_400_no_retry(self):
        add_token_mock()
        responses.get(f"{BASE_URL}/v1/transactions/tx-001", json=ERROR_BODY_400, status=400)

        client = create_client(max_retries=3)
        with pytest.raises(BadRequestError):
            client.transactions.get("tx-001")

        # 1 token + 1 API call (no retries)
        assert len(responses.calls) == 2
