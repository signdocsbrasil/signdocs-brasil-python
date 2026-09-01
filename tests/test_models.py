"""Model deserialization tests using shared fixture data."""

import json
from pathlib import Path

from signdocs_brasil.errors import ProblemDetail
from signdocs_brasil.models.evidence import Evidence
from signdocs_brasil.models.transaction import (
    Transaction,
    TransactionListResponse,
)
from signdocs_brasil.models.webhook import WebhookTestDelivery, WebhookTestResponse

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


class TestWebhookTestResponseDeserialization:
    def test_round_trip_minimal(self):
        payload = {
            "webhookId": "wh_abc",
            "testDelivery": {
                "httpStatus": 200,
                "success": True,
                "timestamp": "2026-04-27T01:23:28.323Z",
            },
        }

        resp = WebhookTestResponse.from_dict(payload)

        assert resp.webhook_id == "wh_abc"
        assert isinstance(resp.test_delivery, WebhookTestDelivery)
        assert resp.test_delivery.http_status == 200
        assert resp.test_delivery.success is True
        assert resp.test_delivery.timestamp == "2026-04-27T01:23:28.323Z"
        assert resp.test_delivery.error is None

        # Round-trip back to camelCase API shape.
        assert resp.to_dict() == payload

    def test_round_trip_with_error(self):
        payload = {
            "webhookId": "wh_xyz",
            "testDelivery": {
                "httpStatus": 502,
                "success": False,
                "error": "Bad Gateway",
                "timestamp": "2026-04-27T01:23:28.323Z",
            },
        }

        resp = WebhookTestResponse.from_dict(payload)

        assert resp.test_delivery.success is False
        assert resp.test_delivery.error == "Bad Gateway"
        assert resp.to_dict() == payload


class TestPolicyBiometricBars:
    """Per-request biometric bars on Policy / PolicyRequest."""

    def test_unset_bars_are_omitted(self):
        from signdocs_brasil.models.transaction import Policy

        # Sending 0 would be rejected by the API, so an unset bar must not
        # appear in the payload at all.
        result = Policy(profile="BIOMETRIC").to_dict()
        assert "minSimilarity" not in result
        assert "minLivenessConfidence" not in result

    def test_bars_round_trip(self):
        from signdocs_brasil.models.transaction import Policy

        policy = Policy.from_dict(
            {"profile": "BIOMETRIC", "minSimilarity": 95, "minLivenessConfidence": 90}
        )
        assert policy.min_similarity == 95
        assert policy.min_liveness_confidence == 90
        assert policy.to_dict() == {
            "profile": "BIOMETRIC",
            "minSimilarity": 95,
            "minLivenessConfidence": 90,
        }

    def test_fractional_bar_passes_through_untouched(self):
        from signdocs_brasil.models.transaction import Policy

        # The API normalises 0.95 and 95 to the same percentage; the SDK must
        # not guess which the caller meant.
        assert Policy(profile="BIOMETRIC", min_similarity=0.95).to_dict()["minSimilarity"] == 0.95

    def test_session_policy_request_carries_bars(self):
        from signdocs_brasil.models.signing_session import PolicyRequest

        assert PolicyRequest(
            profile="BIOMETRIC", min_similarity=99, min_liveness_confidence=95
        ).to_dict() == {
            "profile": "BIOMETRIC",
            "minSimilarity": 99,
            "minLivenessConfidence": 95,
        }


class TestAdvanceSessionSurface:
    """The advance request/response fields that drive a biometric integration."""

    def test_document_photo_request_serialises(self):
        from signdocs_brasil.models.signing_session import AdvanceSessionRequest, DeviceInfo

        req = AdvanceSessionRequest(
            action="complete_document_photo",
            document_image="AA==",
            document_type="RG",
            sandbox_brightness=8,
            sandbox_sharpness=6,
            device_info=DeviceInfo(screen_width=390, language="pt-BR"),
        )
        assert req.to_dict() == {
            "action": "complete_document_photo",
            "documentImage": "AA==",
            "documentType": "RG",
            "sandboxBrightness": 8,
            "sandboxSharpness": 6,
            "deviceInfo": {"screenWidth": 390, "language": "pt-BR"},
        }

    def test_confirm_signer_carries_cpf(self):
        from signdocs_brasil.models.signing_session import AdvanceSessionRequest

        assert AdvanceSessionRequest(
            action="confirm_signer", cpf_cnpj="11144477735"
        ).to_dict() == {"action": "confirm_signer", "cpfCnpj": "11144477735"}

    def test_rejected_step_is_read_from_the_body_not_the_status(self):
        from signdocs_brasil.models.signing_session import AdvanceSessionResponse

        # A rejected biometric step is HTTP 200 with the session still ACTIVE.
        # Anything that only branches on the status reads this as success.
        res = AdvanceSessionResponse.from_dict(
            {
                "sessionId": "ss_1",
                "status": "ACTIVE",
                "errorCode": "BIOMETRIC_MATCH_FAILED",
                "errorDetail": "Não foi possível confirmar seu rosto. Tente novamente.",
                "retryable": True,
            }
        )
        assert res.status == "ACTIVE"
        assert res.error_code == "BIOMETRIC_MATCH_FAILED"
        assert res.retryable is True

    def test_exhausted_attempts_are_not_retryable(self):
        from signdocs_brasil.models.signing_session import AdvanceSessionResponse

        res = AdvanceSessionResponse.from_dict(
            {
                "sessionId": "ss_1",
                "status": "ACTIVE",
                "errorCode": "DOCUMENT_QUALITY_LOW",
                "retryable": False,
            }
        )
        assert res.retryable is False

    def test_fallback_and_autopass_are_parsed(self):
        from signdocs_brasil.models.signing_session import AdvanceSessionResponse

        res = AdvanceSessionResponse.from_dict(
            {
                "sessionId": "ss_1",
                "status": "ACTIVE",
                "sandbox": {"otpCode": "123456", "autoPass": True},
                "fallback": {
                    "triggered": True,
                    "reason": "BIOMETRIC_UNAVAILABLE",
                    "nextStepType": "DOCUMENT_PHOTO_MATCH",
                },
            }
        )
        assert res.sandbox.auto_pass is True
        assert res.fallback.triggered is True
        assert res.fallback.next_step_type == "DOCUMENT_PHOTO_MATCH"

    def test_absent_optional_fields_stay_none(self):
        from signdocs_brasil.models.signing_session import AdvanceSessionResponse

        res = AdvanceSessionResponse.from_dict({"sessionId": "ss_1", "status": "COMPLETED"})
        assert res.error_code is None
        assert res.retryable is None
        assert res.fallback is None


class TestEnrollmentLifecycle:
    """GET / DELETE on an enrolment — the re-enrolment sweep and erasure."""

    def test_status_reports_the_expiry_window(self):
        from signdocs_brasil.models.user import EnrollmentStatusResponse

        res = EnrollmentStatusResponse.from_dict(
            {
                "userExternalId": "emp_001",
                "enrollmentSource": "BANK_PROVIDED",
                "enrollmentVersion": 2,
                "enrollmentHash": "abc",
                "enrolledAt": "2026-08-31T00:00:00.000Z",
                "expiresAt": "2026-11-29T00:00:00.000Z",
                "expired": False,
                "retentionDays": 90,
                "maskedCpf": "***7735",
                "faceConfidence": 99.9,
            }
        )
        assert res.expires_at == "2026-11-29T00:00:00.000Z"
        assert res.expired is False
        assert res.retention_days == 90
        assert res.masked_cpf == "***7735"

    def test_expired_enrolment_is_flagged(self):
        from signdocs_brasil.models.user import EnrollmentStatusResponse

        # This is the whole point of the endpoint: catch it here rather than as
        # a 422 in the middle of a signature.
        res = EnrollmentStatusResponse.from_dict(
            {
                "userExternalId": "emp_002",
                "enrollmentSource": "BANK_PROVIDED",
                "enrollmentVersion": 1,
                "enrollmentHash": "abc",
                "enrolledAt": "2026-01-01T00:00:00.000Z",
                "expiresAt": "2026-04-01T00:00:00.000Z",
                "expired": True,
                "retentionDays": 90,
            }
        )
        assert res.expired is True
        assert res.masked_cpf is None

    def test_delete_reports_every_destroyed_version(self):
        from signdocs_brasil.models.user import DeleteEnrollmentResponse

        # Versioned storage: a plain delete would only write a marker and the
        # image would still be recoverable, so the count matters.
        res = DeleteEnrollmentResponse.from_dict(
            {
                "userExternalId": "emp_001",
                "deleted": True,
                "deletedAt": "2026-08-31T21:00:40.260Z",
                "enrollmentVersion": 2,
                "objectsDeleted": 1,
                "versionsDeleted": 3,
            }
        )
        assert res.deleted is True
        assert res.versions_deleted == 3


class TestBatchEnrollmentDryRun:
    """Screening reference photos before committing them."""

    def test_dry_run_reports_quality_per_row(self):
        from signdocs_brasil.models.user import EnrollUsersBatchResponse

        res = EnrollUsersBatchResponse.from_dict(
            {
                "dryRun": True,
                "submitted": 2,
                "usable": 1,
                "marginal": 1,
                "rejected": 0,
                "results": [
                    {
                        "index": 0,
                        "userExternalId": "matricula-4471",
                        "status": "usable",
                        "faceConfidence": 99.9,
                        "quality": {"brightness": 72, "sharpness": 92},
                        "pose": {"yaw": -3, "pitch": 2, "roll": 1},
                        "faceCoverage": 0.43,
                        "warnings": [],
                    },
                    {
                        "index": 1,
                        "userExternalId": "matricula-4472",
                        "status": "marginal",
                        "quality": {"brightness": 15, "sharpness": 13},
                        "warnings": ["LOW_BRIGHTNESS", "LOW_SHARPNESS"],
                    },
                ],
            }
        )

        assert res.dry_run is True
        assert (res.usable, res.marginal) == (1, 1)
        assert res.results[0].quality.brightness == 72
        assert res.results[0].pose.yaw == -3
        assert res.results[0].face_coverage == 0.43
        # marginal enrols fine today — it is the row that fails matching later
        assert res.results[1].status == "marginal"
        assert "LOW_BRIGHTNESS" in res.results[1].warnings

    def test_real_write_has_no_dry_run_fields(self):
        from signdocs_brasil.models.user import EnrollUsersBatchResponse

        res = EnrollUsersBatchResponse.from_dict(
            {
                "submitted": 1,
                "succeeded": 1,
                "failed": 0,
                "results": [
                    {
                        "index": 0,
                        "userExternalId": "a",
                        "status": "enrolled",
                        "enrollmentVersion": 2,
                    }
                ],
            }
        )

        assert res.dry_run is None
        assert res.succeeded == 1
        assert res.results[0].enrollment_version == 2
        assert res.results[0].quality is None


class TestEnrollmentQualityFeedback:
    """Metrics on a real enrolment, and the PUT dry run."""

    def test_successful_enrolment_still_reports_warnings(self):
        from signdocs_brasil.models.user import EnrollUserResponse

        # The trap: detection confidence is ~100 on a photo that makes a poor
        # reference. Without warnings the caller has no signal at all.
        res = EnrollUserResponse.from_dict(
            {
                "userExternalId": "matricula-4471",
                "enrollmentHash": "h",
                "enrollmentVersion": 1,
                "enrollmentSource": "BANK_PROVIDED",
                "enrolledAt": "2026-09-01T00:00:00.000Z",
                "cpf": "11144477735",
                "faceConfidence": 99.99,
                "quality": {"brightness": 15, "sharpness": 13},
                "pose": {"yaw": 3, "pitch": 6, "roll": 0},
                "faceCoverage": 0.4222,
                "warnings": ["LOW_BRIGHTNESS", "LOW_SHARPNESS"],
            }
        )

        assert res.face_confidence == 99.99
        assert res.quality.brightness == 15
        assert res.pose.pitch == 6
        assert res.face_coverage == 0.4222
        assert res.warnings == ["LOW_BRIGHTNESS", "LOW_SHARPNESS"]

    def test_clean_enrolment_has_empty_warnings(self):
        from signdocs_brasil.models.user import EnrollUserResponse

        res = EnrollUserResponse.from_dict(
            {
                "userExternalId": "a",
                "enrollmentHash": "h",
                "enrollmentVersion": 1,
                "enrollmentSource": "BANK_PROVIDED",
                "enrolledAt": "x",
                "cpf": "11144477735",
                "faceConfidence": 99.9,
                "quality": {"brightness": 72, "sharpness": 92},
                "warnings": [],
            }
        )

        assert res.warnings == []
        assert res.pose is None

    def test_dry_run_verdict(self):
        from signdocs_brasil.models.user import InspectEnrollmentResponse

        res = InspectEnrollmentResponse.from_dict(
            {
                "dryRun": True,
                "userExternalId": "a",
                "status": "marginal",
                "faceConfidence": 99.99,
                "quality": {"brightness": 15, "sharpness": 13},
                "faceCoverage": 0.4222,
                "warnings": ["LOW_BRIGHTNESS"],
            }
        )

        assert res.dry_run is True
        assert res.status == "marginal"
        assert res.quality.sharpness == 13
        assert res.warnings == ["LOW_BRIGHTNESS"]

    def test_dry_run_rejection_carries_the_reason(self):
        from signdocs_brasil.models.user import InspectEnrollmentResponse

        res = InspectEnrollmentResponse.from_dict(
            {"dryRun": True, "status": "rejected", "error": "No face detected", "warnings": []}
        )

        assert res.status == "rejected"
        assert res.error == "No face detected"
        assert res.quality is None


class TestReferenceQuality:
    """One verdict key, same values, wherever it appears."""

    def test_real_enrolment_states_the_verdict(self):
        from signdocs_brasil.models.user import EnrollUserResponse

        res = EnrollUserResponse.from_dict(
            {
                "userExternalId": "a",
                "enrollmentHash": "h",
                "enrollmentVersion": 1,
                "enrollmentSource": "BANK_PROVIDED",
                "enrolledAt": "x",
                "cpf": "11144477735",
                "faceConfidence": 99.99,
                "warnings": ["LOW_BRIGHTNESS"],
                "referenceQuality": "marginal",
            }
        )

        # Stated, not derived from len(warnings).
        assert res.reference_quality == "marginal"

    def test_batch_row_separates_write_outcome_from_photo_verdict(self):
        from signdocs_brasil.models.user import BatchEnrollmentResult

        row = BatchEnrollmentResult.from_dict(
            {
                "index": 0,
                "userExternalId": "a",
                "status": "enrolled",
                "warnings": ["LOW_SHARPNESS"],
                "referenceQuality": "marginal",
            }
        )

        # The combination that matters: it stored fine AND it is a weak
        # reference. One field could not express both.
        assert row.status == "enrolled"
        assert row.reference_quality == "marginal"

    def test_dry_run_carries_the_same_field(self):
        from signdocs_brasil.models.user import InspectEnrollmentResponse

        res = InspectEnrollmentResponse.from_dict(
            {"status": "usable", "warnings": [], "referenceQuality": "usable"}
        )

        assert res.reference_quality == "usable"
