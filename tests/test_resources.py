"""Tests for all resource classes."""

from unittest.mock import MagicMock

import pytest

from signdocs_brasil._http_client import HttpClient
from signdocs_brasil.errors import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    ProblemDetail,
    UnprocessableEntityError,
)
from signdocs_brasil.resources.document_groups import DocumentGroupsResource
from signdocs_brasil.resources.documents import DocumentsResource
from signdocs_brasil.resources.evidence import EvidenceResource
from signdocs_brasil.resources.health import HealthResource
from signdocs_brasil.resources.signing import SigningResource
from signdocs_brasil.resources.steps import StepsResource
from signdocs_brasil.resources.transactions import TransactionsResource
from signdocs_brasil.resources.users import UsersResource
from signdocs_brasil.resources.verification import VerificationResource
from signdocs_brasil.resources.webhooks import WebhooksResource


def mock_http():
    http = MagicMock(spec=HttpClient)
    return http


MOCK_TX = {
    "tenantId": "ten_1",
    "transactionId": "tx_1",
    "status": "DRAFT",
    "purpose": "electronic_signature",
    "policy": {"profile": "standard"},
    "signer": {"name": "Test User", "userExternalId": "ext_1"},
    "expiresAt": "2024-12-31T23:59:59Z",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z",
}


def make_tx(**overrides):
    tx = dict(MOCK_TX)
    tx.update(overrides)
    return tx


MOCK_STEP = {
    "tenantId": "ten_1",
    "transactionId": "tx_1",
    "stepId": "step_1",
    "type": "LIVENESS",
    "status": "PENDING",
    "order": 1,
    "attempts": 0,
    "maxAttempts": 3,
}


class TestTransactionsResource:
    def test_create_uses_idempotency(self):
        http = mock_http()
        http.request_with_idempotency.return_value = make_tx()
        tx = TransactionsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"type": "electronic"}

        tx.create(req)

        http.request_with_idempotency.assert_called_once_with(
            "POST", "/v1/transactions",
            body={"type": "electronic"}, idempotency_key=None, timeout=None,
        )

    def test_create_with_explicit_key(self):
        http = mock_http()
        http.request_with_idempotency.return_value = make_tx()
        tx = TransactionsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"type": "electronic"}

        tx.create(req, idempotency_key="my-key")

        http.request_with_idempotency.assert_called_once_with(
            "POST", "/v1/transactions",
            body={"type": "electronic"}, idempotency_key="my-key", timeout=None,
        )

    def test_list_with_query(self):
        http = mock_http()
        http.request.return_value = {
            "transactions": [make_tx()],
            "count": 1,
        }
        tx = TransactionsResource(http)
        params = MagicMock()
        params.to_query.return_value = {"status": "active", "limit": "10"}

        tx.list(params)

        http.request.assert_called_once_with(
            "GET", "/v1/transactions",
            query={"status": "active", "limit": "10"}, timeout=None,
        )

    def test_get(self):
        http = mock_http()
        http.request.return_value = make_tx()
        tx = TransactionsResource(http)

        tx.get("tx_1")

        http.request.assert_called_once_with("GET", "/v1/transactions/tx_1", timeout=None)

    def test_cancel_delete_with_body(self):
        http = mock_http()
        http.request.return_value = {
            "transactionId": "tx_1",
            "status": "CANCELLED",
            "cancelledAt": "2024-01-01T00:00:00Z",
        }
        tx = TransactionsResource(http)

        result = tx.cancel("tx_1")

        http.request.assert_called_once_with("DELETE", "/v1/transactions/tx_1", timeout=None)
        assert result.transaction_id == "tx_1"
        assert result.status == "CANCELLED"
        assert result.cancelled_at == "2024-01-01T00:00:00Z"

    def test_finalize(self):
        http = mock_http()
        http.request.return_value = {
            "transactionId": "tx_1",
            "status": "COMPLETED",
            "evidenceId": "ev_1",
            "evidenceHash": "abc123hash",
            "completedAt": "2024-01-01T00:00:00Z",
        }
        tx = TransactionsResource(http)

        result = tx.finalize("tx_1")

        http.request.assert_called_once_with(
            "POST", "/v1/transactions/tx_1/finalize", timeout=None,
        )
        assert result.transaction_id == "tx_1"
        assert result.status == "COMPLETED"
        assert result.evidence_id == "ev_1"
        assert result.evidence_hash == "abc123hash"
        assert result.completed_at == "2024-01-01T00:00:00Z"

    def test_list_auto_paginate(self):
        http = mock_http()
        http.request.side_effect = [
            {
                "transactions": [make_tx(transactionId="tx_1"), make_tx(transactionId="tx_2")],
                "count": 3,
                "nextToken": "page2",
            },
            {
                "transactions": [make_tx(transactionId="tx_3")],
                "count": 3,
            },
        ]
        tx = TransactionsResource(http)

        items = list(tx.list_auto_paginate())

        assert len(items) == 3
        assert http.request.call_count == 2


class TestDocumentsResource:
    def test_upload(self):
        http = mock_http()
        http.request.return_value = {
            "transactionId": "tx_1",
            "documentHash": "sha256abc",
            "status": "DOCUMENT_UPLOADED",
            "uploadedAt": "2024-01-01T00:00:00Z",
        }
        docs = DocumentsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"content": "base64data", "filename": "test.pdf"}

        result = docs.upload("tx_1", req)

        http.request.assert_called_once_with(
            "POST", "/v1/transactions/tx_1/document",
            body={"content": "base64data", "filename": "test.pdf"}, timeout=None,
        )
        assert result.transaction_id == "tx_1"
        assert result.document_hash == "sha256abc"
        assert result.status == "DOCUMENT_UPLOADED"
        assert result.uploaded_at == "2024-01-01T00:00:00Z"

    def test_presign(self):
        http = mock_http()
        http.request.return_value = {
            "uploadUrl": "https://s3/upload",
            "uploadToken": "tok_abc",
            "s3Key": "uploads/tx_1/doc.pdf",
            "expiresIn": 3600,
            "contentType": "application/pdf",
            "instructions": "PUT the file to the uploadUrl",
        }
        docs = DocumentsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"contentType": "application/pdf", "filename": "doc.pdf"}

        result = docs.presign("tx_1", req)

        http.request.assert_called_once_with(
            "POST", "/v1/transactions/tx_1/document/presign",
            body={"contentType": "application/pdf", "filename": "doc.pdf"}, timeout=None,
        )
        assert result.upload_url == "https://s3/upload"
        assert result.upload_token == "tok_abc"
        assert result.s3_key == "uploads/tx_1/doc.pdf"
        assert result.expires_in == 3600
        assert result.content_type == "application/pdf"
        assert result.instructions == "PUT the file to the uploadUrl"

    def test_download(self):
        http = mock_http()
        http.request.return_value = {
            "transactionId": "tx_1",
            "documentHash": "sha256abc",
            "originalUrl": "https://s3/original",
            "signedUrl": "https://s3/signed",
            "expiresIn": 3600,
        }
        docs = DocumentsResource(http)

        result = docs.download("tx_1")

        http.request.assert_called_once_with(
            "GET", "/v1/transactions/tx_1/download", timeout=None,
        )
        assert result.transaction_id == "tx_1"
        assert result.document_hash == "sha256abc"
        assert result.original_url == "https://s3/original"
        assert result.signed_url == "https://s3/signed"
        assert result.expires_in == 3600


class TestHealthResource:
    def test_check_no_auth(self):
        http = mock_http()
        http.request.return_value = {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        health = HealthResource(http)

        health.check()

        http.request.assert_called_once_with("GET", "/health", no_auth=True, timeout=None)

    def test_history_no_auth(self):
        http = mock_http()
        http.request.return_value = {"entries": []}
        health = HealthResource(http)

        health.history()

        http.request.assert_called_once_with("GET", "/health/history", no_auth=True, timeout=None)


class TestWebhooksResource:
    def test_register(self):
        http = mock_http()
        http.request.return_value = {
            "webhookId": "wh_1",
            "url": "https://example.com/hook",
            "secret": "whsec_123",
            "events": ["TRANSACTION.COMPLETED"],
            "status": "ACTIVE",
            "createdAt": "2024-01-01T00:00:00Z",
        }
        webhooks = WebhooksResource(http)
        req = MagicMock()
        req.to_dict.return_value = {
            "url": "https://example.com/hook",
            "events": ["TRANSACTION.COMPLETED"],
        }

        webhooks.register(req)

        http.request.assert_called_once_with(
            "POST", "/v1/webhooks",
            body={
                "url": "https://example.com/hook",
                "events": ["TRANSACTION.COMPLETED"],
            },
            timeout=None,
        )

    def test_list(self):
        http = mock_http()
        http.request.return_value = [
            {
                "webhookId": "wh_1", "url": "https://a.com",
                "events": [], "status": "ACTIVE",
                "createdAt": "2024-01-01T00:00:00Z",
            },
            {
                "webhookId": "wh_2", "url": "https://b.com",
                "events": [], "status": "ACTIVE",
                "createdAt": "2024-01-01T00:00:00Z",
            },
        ]
        webhooks = WebhooksResource(http)

        result = webhooks.list()

        http.request.assert_called_once_with("GET", "/v1/webhooks", timeout=None)
        assert len(result) == 2

    def test_delete_204(self):
        http = mock_http()
        http.request.return_value = None
        webhooks = WebhooksResource(http)

        webhooks.delete("wh_1")

        http.request.assert_called_once_with("DELETE", "/v1/webhooks/wh_1", timeout=None)

    def test_test_webhook(self):
        http = mock_http()
        http.request.return_value = {
            "webhookId": "wh_1",
            "testDelivery": {
                "httpStatus": 200,
                "success": True,
                "timestamp": "2026-04-27T01:23:28.323Z",
            },
        }
        webhooks = WebhooksResource(http)

        result = webhooks.test("wh_1")

        http.request.assert_called_once_with("POST", "/v1/webhooks/wh_1/test", timeout=None)
        assert result.webhook_id == "wh_1"
        assert result.test_delivery.http_status == 200
        assert result.test_delivery.success is True
        assert result.test_delivery.timestamp == "2026-04-27T01:23:28.323Z"
        assert result.test_delivery.error is None

    def test_test_webhook_with_error(self):
        http = mock_http()
        http.request.return_value = {
            "webhookId": "wh_1",
            "testDelivery": {
                "httpStatus": 502,
                "success": False,
                "error": "Bad Gateway",
                "timestamp": "2026-04-27T01:23:28.323Z",
            },
        }
        webhooks = WebhooksResource(http)

        result = webhooks.test("wh_1")

        assert result.webhook_id == "wh_1"
        assert result.test_delivery.http_status == 502
        assert result.test_delivery.success is False
        assert result.test_delivery.error == "Bad Gateway"


class TestStepsResource:
    def test_list(self):
        http = mock_http()
        http.request.return_value = {"steps": [dict(MOCK_STEP)]}
        steps = StepsResource(http)

        result = steps.list("tx_1")

        http.request.assert_called_once_with(
            "GET", "/v1/transactions/tx_1/steps", timeout=None,
        )
        assert len(result.steps) == 1

    def test_start(self):
        http = mock_http()
        http.request.return_value = {
            "stepId": "step_1",
            "type": "LIVENESS",
            "status": "IN_PROGRESS",
            "livenessSessionId": "sess_1",
        }
        steps = StepsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"captureMode": "PHOTO"}

        steps.start("tx_1", "step_1", req)

        http.request.assert_called_once()
        call_args = http.request.call_args
        assert call_args[0][0] == "POST"
        assert "/steps/step_1/start" in call_args[0][1]

    def test_complete(self):
        http = mock_http()
        http.request.return_value = dict(
            MOCK_STEP, status="COMPLETED",
            completedAt="2024-01-01T00:00:00Z",
        )
        steps = StepsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"accepted": True}

        steps.complete("tx_1", "step_1", req)

        http.request.assert_called_once()
        call_args = http.request.call_args
        assert call_args[0][0] == "POST"
        assert "/steps/step_1/complete" in call_args[0][1]


class TestSigningResource:
    def test_prepare(self):
        http = mock_http()
        http.request.return_value = {
            "signatureRequestId": "req_1",
            "hashToSign": "abc123",
            "hashAlgorithm": "SHA-256",
            "signatureAlgorithm": "ECDSA",
        }
        signing = SigningResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"certificate_chain": ["cert1"]}

        signing.prepare("tx_1", req)

        http.request.assert_called_once()
        assert "signing/prepare" in http.request.call_args[0][1]

    def test_complete(self):
        http = mock_http()
        http.request.return_value = {
            "stepId": "step_1",
            "status": "COMPLETED",
            "result": {
                "digitalSignature": {
                    "certificateSubject": "CN=Test",
                    "certificateSerial": "123",
                    "certificateIssuer": "CN=CA",
                    "algorithm": "SHA256withECDSA",
                    "signedAt": "2024-01-01T00:00:00Z",
                    "signedPdfHash": "deadbeef",
                    "signatureFieldName": "sig1",
                },
            },
        }
        signing = SigningResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"signature": "sig_data"}

        signing.complete("tx_1", req)

        http.request.assert_called_once()
        assert "signing/complete" in http.request.call_args[0][1]


class TestEvidenceResource:
    def test_get(self):
        http = mock_http()
        http.request.return_value = {
            "tenantId": "ten_1",
            "transactionId": "tx_1",
            "evidenceId": "ev_1",
            "status": "COMPLETE",
            "signer": {"name": "Test User", "userExternalId": "ext_1"},
            "createdAt": "2024-01-01T00:00:00Z",
        }
        evidence = EvidenceResource(http)

        evidence.get("tx_1")

        http.request.assert_called_once_with(
            "GET", "/v1/transactions/tx_1/evidence", timeout=None,
        )


class TestVerificationResource:
    def test_verify_no_auth(self):
        http = mock_http()
        http.request.return_value = {
            "evidenceId": "ev_1",
            "status": "COMPLETE",
            "transactionId": "tx_1",
            "purpose": "DOCUMENT_SIGNATURE",
            "documentHash": "sha256abc",
            "evidenceHash": "sha256def",
            "policy": "CLICK_ONLY",
            "steps": [],
            "signer": {"displayName": "Test User"},
            "tenantName": "Acme Corp",
            "createdAt": "2024-01-01T00:00:00Z",
            "completedAt": "2024-01-01T00:01:00Z",
        }
        verification = VerificationResource(http)

        result = verification.verify("ev_1")

        http.request.assert_called_once_with(
            "GET", "/v1/verify/ev_1", no_auth=True, timeout=None,
        )
        assert result.evidence_id == "ev_1"
        assert result.status == "COMPLETE"
        assert result.transaction_id == "tx_1"
        assert result.purpose == "DOCUMENT_SIGNATURE"
        assert result.signer.display_name == "Test User"
        assert result.tenant_name == "Acme Corp"

    def test_downloads_no_auth(self):
        http = mock_http()
        http.request.return_value = {
            "evidenceId": "ev_1",
            "downloads": {
                "originalDocument": {
                    "url": "https://example.com/original.pdf",
                    "filename": "contrato.pdf",
                },
                "evidencePack": {
                    "url": "https://example.com/evidence-pack.p7m",
                    "filename": "evidence-pack.p7m",
                },
                "finalPdf": {
                    "url": "https://example.com/final.pdf",
                    "filename": "final.pdf",
                },
                "signedSignature": {
                    "url": "https://example.com/signature.p7s",
                    "filename": "signature.p7s",
                },
            },
        }
        verification = VerificationResource(http)

        result = verification.downloads("ev_1")

        http.request.assert_called_once_with(
            "GET", "/v1/verify/ev_1/downloads", no_auth=True, timeout=None,
        )
        assert result.evidence_id == "ev_1"
        assert result.downloads.original_document.filename == "contrato.pdf"
        assert result.downloads.evidence_pack.url == "https://example.com/evidence-pack.p7m"
        assert result.downloads.final_pdf.filename == "final.pdf"
        assert result.downloads.signed_signature.filename == "signature.p7s"

    def test_downloads_envelope_member_omits_signed_signature(self):
        http = mock_http()
        http.request.return_value = {
            "evidenceId": "ev_2",
            "downloads": {
                "originalDocument": None,
                "evidencePack": {
                    "url": "https://example.com/evidence-pack.p7m",
                    "filename": "evidence-pack.p7m",
                },
                "finalPdf": None,
            },
        }
        verification = VerificationResource(http)

        result = verification.downloads("ev_2")

        assert result.downloads.original_document is None
        assert result.downloads.final_pdf is None
        assert result.downloads.signed_signature is None
        assert result.downloads.evidence_pack.filename == "evidence-pack.p7m"

    def test_verify_envelope_no_auth(self):
        http = mock_http()
        http.request.return_value = {
            "envelopeId": "env_1",
            "status": "COMPLETED",
            "signingMode": "SEQUENTIAL",
            "totalSigners": 2,
            "completedSessions": 2,
            "documentHash": "sha256:abc",
            "tenantName": "Acme",
            "tenantCnpj": "12345678000100",
            "signers": [
                {
                    "signerIndex": 1,
                    "displayName": "João Silva",
                    "cpfCnpj": "12345678901",
                    "status": "COMPLETED",
                    "policyProfile": "DIGITAL_CERTIFICATE",
                    "evidenceId": "ev_a",
                    "completedAt": "2026-04-13T18:00:00Z",
                },
                {
                    "signerIndex": 2,
                    "displayName": "Maria Souza",
                    "status": "COMPLETED",
                    "evidenceId": "ev_b",
                    "completedAt": "2026-04-13T18:30:00Z",
                },
            ],
            "downloads": {
                "consolidatedSignature": {
                    "url": "https://example.com/envelope-signature.p7s",
                    "filename": "signature.p7s",
                },
            },
            "createdAt": "2026-04-13T17:00:00Z",
            "completedAt": "2026-04-13T18:30:00Z",
        }
        verification = VerificationResource(http)

        result = verification.verify_envelope("env_1")

        http.request.assert_called_once_with(
            "GET", "/v1/verify/envelope/env_1", no_auth=True, timeout=None,
        )
        assert result.envelope_id == "env_1"
        assert result.signing_mode == "SEQUENTIAL"
        assert result.total_signers == 2
        assert len(result.signers) == 2
        assert result.signers[0].display_name == "João Silva"
        assert result.signers[0].cpf_cnpj == "12345678901"
        assert result.signers[1].evidence_id == "ev_b"
        assert result.downloads is not None
        assert result.downloads.consolidated_signature is not None
        assert result.downloads.consolidated_signature.filename == "signature.p7s"
        assert result.downloads.combined_signed_pdf is None


class TestUsersResource:
    def test_enroll_put(self):
        http = mock_http()
        http.request.return_value = {
            "userExternalId": "ext_1",
            "enrollmentHash": "sha256enroll",
            "enrollmentVersion": 1,
            "enrollmentSource": "BANK_PROVIDED",
            "enrolledAt": "2024-01-01T00:00:00Z",
            "cpf": "12345678901",
            "faceConfidence": 0.98,
        }
        users = UsersResource(http)
        req = MagicMock()
        req.to_dict.return_value = {
            "image": "base64data", "cpf": "12345678901", "source": "BANK_PROVIDED",
        }

        result = users.enroll("ext_1", req)

        http.request.assert_called_once()
        call_args = http.request.call_args
        assert call_args[0][0] == "PUT"
        assert "/users/ext_1/enrollment" in call_args[0][1]
        assert result.user_external_id == "ext_1"
        assert result.enrollment_hash == "sha256enroll"
        assert result.enrollment_version == 1
        assert result.enrollment_source == "BANK_PROVIDED"
        assert result.cpf == "12345678901"
        assert result.face_confidence == 0.98


class TestDocumentGroupsResource:
    def test_combined_stamp(self):
        http = mock_http()
        http.request.return_value = {
            "groupId": "grp_1",
            "signerCount": 3,
            "downloadUrl": "https://example.com/stamp.pdf",
            "expiresIn": 3600,
        }
        groups = DocumentGroupsResource(http)

        result = groups.combined_stamp("grp_1")

        http.request.assert_called_once()
        assert "document-groups/grp_1/combined-stamp" in http.request.call_args[0][1]
        assert result.group_id == "grp_1"
        assert result.signer_count == 3
        assert result.download_url == "https://example.com/stamp.pdf"
        assert result.expires_in == 3600


# Phase 3: Error path tests
class TestTransactionsResourceErrors:
    def test_create_400_bad_request(self):
        http = mock_http()
        http.request_with_idempotency.side_effect = BadRequestError(
            ProblemDetail(type="about:blank", title="Bad Request", status=400, detail="Invalid")
        )
        tx = TransactionsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"type": "electronic"}

        with pytest.raises(BadRequestError):
            tx.create(req)

    def test_get_404_not_found(self):
        http = mock_http()
        http.request.side_effect = NotFoundError(
            ProblemDetail(type="about:blank", title="Not Found", status=404)
        )
        tx = TransactionsResource(http)

        with pytest.raises(NotFoundError):
            tx.get("nonexistent")

    def test_create_409_conflict(self):
        http = mock_http()
        http.request_with_idempotency.side_effect = ConflictError(
            ProblemDetail(type="about:blank", title="Conflict", status=409)
        )
        tx = TransactionsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"type": "electronic"}

        with pytest.raises(ConflictError):
            tx.create(req)


class TestDocumentsResourceErrors:
    def test_upload_422_unprocessable(self):
        http = mock_http()
        http.request.side_effect = UnprocessableEntityError(
            ProblemDetail(
                type="about:blank", title="Unprocessable",
                status=422, detail="CPF invalid",
            )
        )
        docs = DocumentsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"content": "base64", "filename": "doc.pdf"}

        with pytest.raises(UnprocessableEntityError):
            docs.upload("tx_1", req)

    def test_confirm_400_bad_request(self):
        http = mock_http()
        http.request.side_effect = BadRequestError(
            ProblemDetail(type="about:blank", title="Bad Request", status=400)
        )
        docs = DocumentsResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"sha256Hash": "abc"}

        with pytest.raises(BadRequestError):
            docs.confirm("tx_1", req)


class TestWebhooksResourceErrors:
    def test_register_400_bad_request(self):
        http = mock_http()
        http.request.side_effect = BadRequestError(
            ProblemDetail(type="about:blank", title="Bad Request", status=400, detail="Invalid URL")
        )
        webhooks = WebhooksResource(http)
        req = MagicMock()
        req.to_dict.return_value = {"url": "not-a-url", "events": []}

        with pytest.raises(BadRequestError):
            webhooks.register(req)


# Phase 6: Pagination edge cases
class TestTransactionsPaginationEdgeCases:
    def test_empty_first_page(self):
        http = mock_http()
        http.request.return_value = {"transactions": [], "count": 0}
        tx = TransactionsResource(http)

        result = tx.list()

        assert len(result.transactions) == 0
        assert result.count == 0

    def test_single_page_no_next_token(self):
        http = mock_http()
        http.request.return_value = {
            "transactions": [make_tx()],
            "count": 1,
        }
        tx = TransactionsResource(http)

        result = tx.list()

        assert len(result.transactions) == 1
        assert result.next_token is None

    def test_auto_paginate_single_page(self):
        http = mock_http()
        http.request.return_value = {
            "transactions": [make_tx(transactionId="tx_1"), make_tx(transactionId="tx_2")],
            "count": 2,
        }
        tx = TransactionsResource(http)

        items = list(tx.list_auto_paginate())

        assert len(items) == 2
        assert http.request.call_count == 1
