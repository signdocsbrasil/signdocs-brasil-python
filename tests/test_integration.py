"""Integration tests: full stack Config → Client → Auth → Http → Retry → Resource → Model."""

import json
import os

import pytest
import responses

from signdocs_brasil._config import ClientConfig
from signdocs_brasil.client import SignDocsBrasilClient
from signdocs_brasil.errors import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    RateLimitError,
)
from signdocs_brasil.models.document import UploadDocumentRequest
from signdocs_brasil.models.transaction import (
    CreateTransactionRequest,
    Policy,
    Signer,
    TransactionListParams,
)
from signdocs_brasil.models.webhook import RegisterWebhookRequest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")
BASE_URL = "https://api.signdocs.com.br"
TOKEN_URL = f"{BASE_URL}/oauth2/token"

TOKEN_RESPONSE = {
    "access_token": "test-integration-token",
    "token_type": "Bearer",
    "expires_in": 900,
    "scope": "transactions:read transactions:write",
}


def load_fixture(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, f"{name}.json")) as f:
        return json.load(f)


def create_client() -> SignDocsBrasilClient:
    return SignDocsBrasilClient(
        ClientConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
            base_url=BASE_URL,
            max_retries=0,
        )
    )


def add_token_mock():
    responses.post(TOKEN_URL, json=TOKEN_RESPONSE, status=200)


class TestIntegrationHappyPaths:
    @responses.activate
    def test_transactions_create_full_stack(self):
        fixture = load_fixture("transactions-create")
        add_token_mock()
        responses.post(
            f"{BASE_URL}/v1/transactions",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
        )

        client = create_client()
        result = client.transactions.create(
            CreateTransactionRequest(
                purpose="DOCUMENT_SIGNATURE",
                policy=Policy(profile="CLICK_ONLY"),
                signer=Signer(
                    name="João Silva",
                    email="joao@example.com",
                    user_external_id="user-ext-001",
                    cpf="12345678901",
                ),
                metadata={"contractId": "CTR-2024-001"},
            )
        )

        # Verify deserialized model fields
        assert result.tenant_id == "abc123"
        assert result.transaction_id == "tx-uuid-001"
        assert result.status == "CREATED"
        assert result.purpose == "DOCUMENT_SIGNATURE"
        assert result.policy.profile == "CLICK_ONLY"
        assert result.signer.name == "João Silva"
        assert result.signer.email == "joao@example.com"
        assert result.signer.cpf == "12345678901"
        assert len(result.steps) == 1
        assert result.steps[0].step_id == "step-uuid-001"
        assert result.steps[0].type == "CLICK_ACCEPT"
        assert result.steps[0].status == "PENDING"
        assert result.metadata == {"contractId": "CTR-2024-001"}

        # Verify request
        api_call = responses.calls[1].request
        assert api_call.headers["Authorization"] == "Bearer test-integration-token"
        assert "X-Idempotency-Key" in api_call.headers
        body = json.loads(api_call.body)
        assert body["purpose"] == "DOCUMENT_SIGNATURE"
        assert body["signer"]["name"] == "João Silva"

    @responses.activate
    def test_transactions_list_with_pagination(self):
        fixture = load_fixture("transactions-list")
        add_token_mock()
        responses.get(
            f"{BASE_URL}/v1/transactions",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
        )

        client = create_client()
        result = client.transactions.list(
            TransactionListParams(status="COMPLETED", limit=2)
        )

        assert len(result.transactions) == 2
        assert result.count == 2
        assert result.next_token is not None
        assert result.transactions[0].transaction_id == "tx-uuid-002"
        assert result.transactions[0].signer.name == "Maria Santos"
        assert result.transactions[1].policy.profile == "BIOMETRIC"

    @responses.activate
    def test_transactions_get_with_completed_steps(self):
        fixture = load_fixture("transactions-get")
        add_token_mock()
        responses.get(
            f"{BASE_URL}/v1/transactions/tx-uuid-001",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
        )

        client = create_client()
        result = client.transactions.get("tx-uuid-001")

        assert result.status == "IN_PROGRESS"
        assert len(result.steps) == 2
        assert result.steps[0].status == "COMPLETED"
        assert result.steps[0].result is not None
        assert result.steps[0].result.click.accepted is True
        assert result.steps[1].type == "OTP_CHALLENGE"
        assert result.steps[1].status == "PENDING"

    @responses.activate
    def test_documents_upload_full_stack(self):
        fixture = load_fixture("documents-upload")
        add_token_mock()
        responses.post(
            f"{BASE_URL}/v1/transactions/tx-uuid-001/document",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
        )

        client = create_client()
        result = client.documents.upload(
            "tx-uuid-001",
            UploadDocumentRequest(
                content=fixture["input"]["content"],
                filename=fixture["input"]["filename"],
            ),
        )

        assert result.status == "DOCUMENT_UPLOADED"
        assert result.transaction_id == "tx-uuid-001"
        assert result.document_hash == "sha256-abc123def456"
        assert result.uploaded_at == "2024-11-15T00:00:30.000Z"

        api_call = responses.calls[1].request
        body = json.loads(api_call.body)
        assert body["content"] == fixture["input"]["content"]
        assert body["filename"] == "contract.pdf"

    @responses.activate
    def test_webhooks_register_full_stack(self):
        fixture = load_fixture("webhooks-register")
        add_token_mock()
        responses.post(
            f"{BASE_URL}/v1/webhooks",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
        )

        client = create_client()
        result = client.webhooks.register(
            RegisterWebhookRequest(
                url="https://example.com/webhooks/signdocs",
                events=["TRANSACTION.COMPLETED", "TRANSACTION.FAILED"],
            )
        )

        assert result.webhook_id == "wh-uuid-001"
        assert result.url == "https://example.com/webhooks/signdocs"
        assert result.secret == "whsec_generated_secret_abc123"
        assert result.events == ["TRANSACTION.COMPLETED", "TRANSACTION.FAILED"]
        assert result.status == "ACTIVE"

    @responses.activate
    def test_health_check_no_auth(self):
        fixture = load_fixture("health-check")
        # No token mock needed - health check doesn't require auth
        responses.get(
            f"{BASE_URL}/health",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
        )

        client = create_client()
        result = client.health.check()

        assert result.status == "healthy"
        assert result.version == "1.0.0"
        assert result.services is not None
        assert result.services["dynamodb"].status == "healthy"

        # Verify no auth header
        assert "Authorization" not in responses.calls[0].request.headers

    @responses.activate
    def test_verification_verify_no_auth(self):
        fixture = load_fixture("verification-verify")
        responses.get(
            f"{BASE_URL}/v1/verify/ev-uuid-001",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
        )

        client = create_client()
        result = client.verification.verify("ev-uuid-001")

        assert result.evidence_id == "ev-uuid-001"
        assert result.status == "COMPLETED"
        assert result.transaction_id == "tx-uuid-001"
        assert result.purpose == "DOCUMENT_SIGNATURE"
        assert result.signer.display_name == "João Silva"
        assert result.tenant_name == "Acme Corp"

        assert "Authorization" not in responses.calls[0].request.headers


class TestIntegrationErrorPaths:
    @responses.activate
    def test_400_bad_request_with_problem_detail(self):
        fixture = load_fixture("error-400")
        add_token_mock()
        responses.post(
            f"{BASE_URL}/v1/transactions",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
            headers=fixture["response"]["headers"],
        )

        client = create_client()
        with pytest.raises(BadRequestError) as exc_info:
            client.transactions.create(
                CreateTransactionRequest(
                    purpose="DOCUMENT_SIGNATURE",
                    policy=Policy(profile="CLICK_ONLY"),
                    signer=Signer(name="Test", user_external_id="u1"),
                )
            )

        err = exc_info.value
        assert err.status == 400
        assert err.type == fixture["expected_error"]["type"]
        assert err.title == fixture["expected_error"]["title"]
        assert err.detail == fixture["expected_error"]["detail"]

    @responses.activate
    def test_404_not_found(self):
        fixture = load_fixture("error-404")
        add_token_mock()
        responses.get(
            f"{BASE_URL}/v1/transactions/tx-nonexistent",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
            headers=fixture["response"]["headers"],
        )

        client = create_client()
        with pytest.raises(NotFoundError):
            client.transactions.get("tx-nonexistent")

    @responses.activate
    def test_429_rate_limit_with_retry_after(self):
        fixture = load_fixture("error-429")
        add_token_mock()
        responses.post(
            f"{BASE_URL}/v1/transactions",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
            headers=fixture["response"]["headers"],
        )

        client = create_client()
        with pytest.raises(RateLimitError) as exc_info:
            client.transactions.create(
                CreateTransactionRequest(
                    purpose="DOCUMENT_SIGNATURE",
                    policy=Policy(profile="CLICK_ONLY"),
                    signer=Signer(name="Test", user_external_id="u1"),
                )
            )

        assert exc_info.value.retry_after_seconds == 5
        assert exc_info.value.status == 429

    @responses.activate
    def test_409_conflict(self):
        fixture = load_fixture("error-409")
        add_token_mock()
        responses.post(
            f"{BASE_URL}/v1/transactions",
            json=fixture["response"]["body"],
            status=fixture["response"]["status"],
            headers=fixture["response"]["headers"],
        )

        client = create_client()
        with pytest.raises(ConflictError):
            client.transactions.create(
                CreateTransactionRequest(
                    purpose="DOCUMENT_SIGNATURE",
                    policy=Policy(profile="CLICK_ONLY"),
                    signer=Signer(name="Test", user_external_id="u1"),
                )
            )
