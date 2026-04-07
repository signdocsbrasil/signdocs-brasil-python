"""Phase 3: Resource error path tests for the Python SDK."""
from unittest.mock import MagicMock

import pytest

from signdocs_brasil._http_client import HttpClient
from signdocs_brasil.errors import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    ProblemDetail,
    RateLimitError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from signdocs_brasil.resources.document_groups import DocumentGroupsResource
from signdocs_brasil.resources.documents import DocumentsResource
from signdocs_brasil.resources.evidence import EvidenceResource
from signdocs_brasil.resources.signing import SigningResource
from signdocs_brasil.resources.steps import StepsResource
from signdocs_brasil.resources.transactions import TransactionsResource
from signdocs_brasil.resources.users import UsersResource
from signdocs_brasil.resources.webhooks import WebhooksResource


def mock_http():
    return MagicMock(spec=HttpClient)


def make_problem(status, title, detail):
    return ProblemDetail(
        type=f"https://api.signdocs.com.br/errors/{title.lower().replace(' ', '-')}",
        title=title,
        status=status,
        detail=detail,
        instance="/v1/test",
    )


class TestTransactionsErrorPaths:
    def test_create_400_invalid_policy(self):
        http = mock_http()
        http.request_with_idempotency.side_effect = BadRequestError(
            make_problem(400, "Bad Request", "Invalid policy profile: UNKNOWN_PROFILE"),
        )
        tx = TransactionsResource(http)

        with pytest.raises(BadRequestError) as exc_info:
            tx.create(MagicMock(to_dict=MagicMock(return_value={})))
        assert exc_info.value.status == 400
        assert "Invalid policy profile" in exc_info.value.detail

    def test_get_404_nonexistent(self):
        http = mock_http()
        http.request.side_effect = NotFoundError(
            make_problem(404, "Not Found", "Transaction tx-nonexistent not found"),
        )
        tx = TransactionsResource(http)

        with pytest.raises(NotFoundError) as exc_info:
            tx.get("tx-nonexistent")
        assert exc_info.value.status == 404

    def test_create_409_conflict(self):
        http = mock_http()
        http.request_with_idempotency.side_effect = ConflictError(
            make_problem(409, "Conflict", "Transaction tx-uuid-001 is already finalized"),
        )
        tx = TransactionsResource(http)

        with pytest.raises(ConflictError) as exc_info:
            tx.create(MagicMock(to_dict=MagicMock(return_value={})))
        assert exc_info.value.status == 409
        assert "already finalized" in exc_info.value.detail

    def test_finalize_409_already_finalized(self):
        http = mock_http()
        http.request.side_effect = ConflictError(
            make_problem(409, "Conflict", "Transaction tx_1 is already finalized"),
        )
        tx = TransactionsResource(http)

        with pytest.raises(ConflictError):
            tx.finalize("tx_1")

    def test_cancel_400_wrong_state(self):
        http = mock_http()
        http.request.side_effect = BadRequestError(
            make_problem(400, "Bad Request", "Transaction cannot be cancelled in current state"),
        )
        tx = TransactionsResource(http)

        with pytest.raises(BadRequestError):
            tx.cancel("tx_1")

    def test_list_403_insufficient_scope(self):
        http = mock_http()
        http.request.side_effect = ForbiddenError(
            make_problem(403, "Forbidden", "Missing required scope: transactions:read"),
        )
        tx = TransactionsResource(http)

        with pytest.raises(ForbiddenError) as exc_info:
            tx.list()
        assert "transactions:read" in exc_info.value.detail

    def test_list_429_rate_limit(self):
        http = mock_http()
        err = RateLimitError(
            make_problem(429, "Too Many Requests", "Rate limit exceeded"),
            retry_after_seconds=10,
        )
        http.request.side_effect = err
        tx = TransactionsResource(http)

        with pytest.raises(RateLimitError) as exc_info:
            tx.list()
        assert exc_info.value.retry_after_seconds == 10

    def test_get_500_internal_error(self):
        http = mock_http()
        http.request.side_effect = InternalServerError(
            make_problem(500, "Internal Server Error", "Unexpected error"),
        )
        tx = TransactionsResource(http)

        with pytest.raises(InternalServerError):
            tx.get("tx_1")

    def test_list_401_expired_token(self):
        http = mock_http()
        http.request.side_effect = UnauthorizedError(
            make_problem(401, "Unauthorized", "Token expired"),
        )
        tx = TransactionsResource(http)

        with pytest.raises(UnauthorizedError):
            tx.list()


class TestDocumentsErrorPaths:
    def test_upload_422_invalid_cpf(self):
        http = mock_http()
        http.request.side_effect = UnprocessableEntityError(
            make_problem(422, "Unprocessable Entity", "CPF must be exactly 11 digits"),
        )
        docs = DocumentsResource(http)

        with pytest.raises(UnprocessableEntityError) as exc_info:
            docs.upload("tx_1", MagicMock(to_dict=MagicMock(return_value={})))
        assert "CPF" in exc_info.value.detail

    def test_confirm_400_missing_hash(self):
        http = mock_http()
        http.request.side_effect = BadRequestError(
            make_problem(400, "Bad Request", "Missing sha256Hash field"),
        )
        docs = DocumentsResource(http)

        with pytest.raises(BadRequestError):
            docs.confirm("tx_1", MagicMock(to_dict=MagicMock(return_value={})))

    def test_download_404_nonexistent(self):
        http = mock_http()
        http.request.side_effect = NotFoundError(
            make_problem(404, "Not Found", "Transaction not found"),
        )
        docs = DocumentsResource(http)

        with pytest.raises(NotFoundError):
            docs.download("tx-nonexistent")

    def test_presign_400_invalid_content_type(self):
        http = mock_http()
        http.request.side_effect = BadRequestError(
            make_problem(400, "Bad Request", "contentType must be application/pdf"),
        )
        docs = DocumentsResource(http)

        with pytest.raises(BadRequestError) as exc_info:
            mock_req = MagicMock(to_dict=MagicMock(return_value={
                "contentType": "text/plain", "filename": "doc.txt",
            }))
            docs.presign("tx_1", mock_req)
        assert "application/pdf" in exc_info.value.detail


class TestWebhooksErrorPaths:
    def test_register_400_http_url(self):
        http = mock_http()
        http.request.side_effect = BadRequestError(
            make_problem(400, "Bad Request", "URL must be HTTPS"),
        )
        wh = WebhooksResource(http)

        with pytest.raises(BadRequestError) as exc_info:
            wh.register(MagicMock(to_dict=MagicMock(return_value={})))
        assert "HTTPS" in exc_info.value.detail

    def test_delete_404_nonexistent(self):
        http = mock_http()
        http.request.side_effect = NotFoundError(
            make_problem(404, "Not Found", "Webhook not found"),
        )
        wh = WebhooksResource(http)

        with pytest.raises(NotFoundError):
            wh.delete("wh-nonexistent")

    def test_test_400_disabled_webhook(self):
        http = mock_http()
        http.request.side_effect = BadRequestError(
            make_problem(400, "Bad Request", "Webhook is disabled"),
        )
        wh = WebhooksResource(http)

        with pytest.raises(BadRequestError):
            wh.test("wh_1")


class TestStepsErrorPaths:
    def test_start_404_nonexistent(self):
        http = mock_http()
        http.request.side_effect = NotFoundError(
            make_problem(404, "Not Found", "Step step-nonexistent not found"),
        )
        s = StepsResource(http)

        with pytest.raises(NotFoundError):
            s.start("tx_1", "step-nonexistent")

    def test_complete_409_already_completed(self):
        http = mock_http()
        http.request.side_effect = ConflictError(
            make_problem(409, "Conflict", "Step is already completed"),
        )
        s = StepsResource(http)

        with pytest.raises(ConflictError):
            s.complete("tx_1", "step_1", MagicMock(to_dict=MagicMock(return_value={})))

    def test_complete_422_wrong_otp(self):
        http = mock_http()
        http.request.side_effect = UnprocessableEntityError(
            make_problem(422, "Unprocessable Entity", "Invalid OTP code"),
        )
        s = StepsResource(http)

        with pytest.raises(UnprocessableEntityError):
            s.complete("tx_1", "step_1", MagicMock(to_dict=MagicMock(return_value={})))


class TestSigningErrorPaths:
    def test_prepare_400_empty_cert_chain(self):
        http = mock_http()
        http.request.side_effect = BadRequestError(
            make_problem(400, "Bad Request", "certificateChainPems must not be empty"),
        )
        sig = SigningResource(http)

        with pytest.raises(BadRequestError):
            sig.prepare("tx_1", MagicMock(to_dict=MagicMock(return_value={})))

    def test_complete_422_invalid_signature(self):
        http = mock_http()
        http.request.side_effect = UnprocessableEntityError(
            make_problem(422, "Unprocessable Entity", "Invalid raw signature"),
        )
        sig = SigningResource(http)

        with pytest.raises(UnprocessableEntityError):
            sig.complete("tx_1", MagicMock(to_dict=MagicMock(return_value={})))


class TestEvidenceErrorPaths:
    def test_get_404_no_evidence(self):
        http = mock_http()
        http.request.side_effect = NotFoundError(
            make_problem(404, "Not Found", "Evidence not found for transaction tx_1"),
        )
        ev = EvidenceResource(http)

        with pytest.raises(NotFoundError):
            ev.get("tx_1")

    def test_get_403_missing_scope(self):
        http = mock_http()
        http.request.side_effect = ForbiddenError(
            make_problem(403, "Forbidden", "Missing required scope: evidence:read"),
        )
        ev = EvidenceResource(http)

        with pytest.raises(ForbiddenError) as exc_info:
            ev.get("tx_1")
        assert "evidence:read" in exc_info.value.detail


class TestUsersErrorPaths:
    def test_enroll_422_invalid_image(self):
        http = mock_http()
        http.request.side_effect = UnprocessableEntityError(
            make_problem(422, "Unprocessable Entity", "Image must be a valid JPEG base64"),
        )
        users = UsersResource(http)

        with pytest.raises(UnprocessableEntityError) as exc_info:
            users.enroll("usr_1", MagicMock(to_dict=MagicMock(return_value={})))
        assert "JPEG" in exc_info.value.detail


class TestDocumentGroupsErrorPaths:
    def test_combined_stamp_404_nonexistent(self):
        http = mock_http()
        http.request.side_effect = NotFoundError(
            make_problem(404, "Not Found", "Document group not found"),
        )
        grp = DocumentGroupsResource(http)

        with pytest.raises(NotFoundError):
            grp.combined_stamp("grp-nonexistent")

    def test_combined_stamp_409_not_fully_signed(self):
        http = mock_http()
        http.request.side_effect = ConflictError(
            make_problem(409, "Conflict", "Not all signers have completed signing"),
        )
        grp = DocumentGroupsResource(http)

        with pytest.raises(ConflictError):
            grp.combined_stamp("grp_1")
