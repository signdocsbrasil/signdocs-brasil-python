"""Model deserialization tests using shared fixture data."""

import json
from pathlib import Path

from signdocs_brasil.errors import ProblemDetail
from signdocs_brasil.models.evidence import Evidence
from signdocs_brasil.models.transaction import (
    Transaction,
    TransactionListResponse,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / f"{name}.json") as f:
        return json.load(f)


class TestTransactionDeserialization:
    def test_transaction_from_create_fixture(self):
        fixture = load_fixture("transactions-create")
        tx = Transaction.from_dict(fixture["response"]["body"])

        assert tx.tenant_id == "abc123"
        assert tx.transaction_id == "tx-uuid-001"
        assert tx.status == "CREATED"
        assert tx.purpose == "DOCUMENT_SIGNATURE"
        assert tx.policy.profile == "CLICK_ONLY"
        assert tx.signer.name == "João Silva"
        assert tx.signer.email == "joao@example.com"
        assert tx.signer.user_external_id == "user-ext-001"
        assert tx.signer.cpf == "12345678901"
        assert len(tx.steps) == 1
        assert tx.steps[0].step_id == "step-uuid-001"
        assert tx.steps[0].type == "CLICK_ACCEPT"
        assert tx.steps[0].status == "PENDING"
        assert tx.steps[0].order == 1
        assert tx.steps[0].attempts == 0
        assert tx.steps[0].max_attempts == 3
        assert tx.metadata == {"contractId": "CTR-2024-001"}
        assert tx.expires_at == "2024-11-16T00:00:00.000Z"
        assert tx.created_at == "2024-11-15T00:00:00.000Z"

    def test_transaction_from_get_fixture_with_nested_step_results(self):
        fixture = load_fixture("transactions-get")
        tx = Transaction.from_dict(fixture["response"]["body"])

        assert tx.status == "IN_PROGRESS"
        assert len(tx.steps) == 2

        completed_step = tx.steps[0]
        assert completed_step.status == "COMPLETED"
        assert completed_step.result is not None
        assert completed_step.result.click is not None
        assert completed_step.result.click.accepted is True
        assert completed_step.result.click.text_version == "v1.0"
        assert completed_step.completed_at == "2024-11-15T00:01:00.000Z"

        pending_step = tx.steps[1]
        assert pending_step.type == "OTP_CHALLENGE"
        assert pending_step.status == "PENDING"
        assert pending_step.result is None

    def test_transaction_minimal_fields(self):
        minimal = {
            "tenantId": "abc",
            "transactionId": "tx-1",
            "status": "CREATED",
            "purpose": "DOCUMENT_SIGNATURE",
            "policy": {"profile": "CLICK_ONLY"},
            "signer": {"name": "Test", "userExternalId": "u1"},
            "steps": [],
            "expiresAt": "2024-12-31T00:00:00Z",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }
        tx = Transaction.from_dict(minimal)

        assert tx.metadata is None
        assert tx.document_group_id is None
        assert tx.signer_index is None
        assert tx.total_signers is None

    def test_transaction_list_response_with_pagination(self):
        fixture = load_fixture("transactions-list")
        resp = TransactionListResponse.from_dict(fixture["response"]["body"])

        assert len(resp.transactions) == 2
        assert resp.count == 2
        assert resp.next_token is not None
        assert resp.transactions[0].signer.name == "Maria Santos"
        assert resp.transactions[1].policy.profile == "BIOMETRIC"


class TestProblemDetailDeserialization:
    def test_from_error_400_fixture(self):
        fixture = load_fixture("error-400")
        pd = ProblemDetail.from_dict(fixture["response"]["body"])

        assert pd.type == "https://api.signdocs.com.br/errors/bad-request"
        assert pd.title == "Bad Request"
        assert pd.status == 400
        assert pd.detail == "Invalid policy profile: UNKNOWN_PROFILE"
        assert pd.instance == "/v1/transactions"


class TestEvidenceDeserialization:
    def test_evidence_from_fixture(self):
        fixture = load_fixture("evidence-get")
        ev = Evidence.from_dict(fixture["response"]["body"])

        assert ev.tenant_id == "abc123"
        assert ev.evidence_id == "ev-uuid-001"
        assert ev.signer.name == "João Silva"
        assert ev.signer.cpf == "12345678901"
        assert len(ev.steps) == 1
        assert ev.steps[0].type == "CLICK_ACCEPT"
        assert ev.steps[0].result["click"]["accepted"] is True
        assert ev.document is not None
        assert ev.document.hash is not None
        assert ev.document.filename == "contract.pdf"
