"""Envelope data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CreateEnvelopeRequest:
    """Request to create an envelope for multi-signer signing."""
    signing_mode: str  # PARALLEL or SEQUENTIAL
    total_signers: int
    document_content: str  # base64
    document_filename: str | None = None
    return_url: str | None = None
    cancel_url: str | None = None
    metadata: dict[str, str] | None = None
    locale: str | None = None
    expires_in_minutes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "signingMode": self.signing_mode,
            "totalSigners": self.total_signers,
            "document": {"content": self.document_content},
        }
        if self.document_filename is not None:
            d["document"]["filename"] = self.document_filename
        if self.return_url is not None:
            d["returnUrl"] = self.return_url
        if self.cancel_url is not None:
            d["cancelUrl"] = self.cancel_url
        if self.metadata is not None:
            d["metadata"] = self.metadata
        if self.locale is not None:
            d["locale"] = self.locale
        if self.expires_in_minutes is not None:
            d["expiresInMinutes"] = self.expires_in_minutes
        return d


@dataclass
class Envelope:
    """Envelope returned from create."""
    envelope_id: str
    status: str
    signing_mode: str
    total_signers: int
    document_hash: str
    created_at: str
    expires_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Envelope:
        return cls(
            envelope_id=data["envelopeId"],
            status=data["status"],
            signing_mode=data["signingMode"],
            total_signers=data["totalSigners"],
            document_hash=data["documentHash"],
            created_at=data["createdAt"],
            expires_at=data["expiresAt"],
        )


@dataclass
class AddEnvelopeSessionRequest:
    """Request to add a signer session to an envelope."""
    signer_name: str
    signer_cpf: str | None = None
    signer_cnpj: str | None = None
    signer_email: str | None = None
    signer_phone: str | None = None
    signer_birth_date: str | None = None
    signer_user_external_id: str = "sdk"
    signer_otp_channel: str | None = None
    policy_profile: str = "CLICK_ONLY"
    purpose: str = "DOCUMENT_SIGNATURE"
    signer_index: int = 1
    return_url: str | None = None
    cancel_url: str | None = None
    metadata: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        signer: dict[str, Any] = {
            "name": self.signer_name,
            "userExternalId": self.signer_user_external_id,
        }
        if self.signer_cpf is not None:
            signer["cpf"] = self.signer_cpf
        if self.signer_cnpj is not None:
            signer["cnpj"] = self.signer_cnpj
        if self.signer_email is not None:
            signer["email"] = self.signer_email
        if self.signer_phone is not None:
            signer["phone"] = self.signer_phone
        if self.signer_birth_date is not None:
            signer["birthDate"] = self.signer_birth_date
        if self.signer_otp_channel is not None:
            signer["otpChannel"] = self.signer_otp_channel

        d: dict[str, Any] = {
            "signer": signer,
            "policy": {"profile": self.policy_profile},
            "purpose": self.purpose,
            "signerIndex": self.signer_index,
        }
        if self.return_url is not None:
            d["returnUrl"] = self.return_url
        if self.cancel_url is not None:
            d["cancelUrl"] = self.cancel_url
        if self.metadata is not None:
            d["metadata"] = self.metadata
        return d


@dataclass
class EnvelopeSession:
    """Session added to an envelope."""
    session_id: str
    transaction_id: str
    signer_index: int
    status: str
    url: str
    client_secret: str
    expires_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvelopeSession:
        return cls(
            session_id=data["sessionId"],
            transaction_id=data["transactionId"],
            signer_index=data["signerIndex"],
            status=data["status"],
            url=data["url"],
            client_secret=data["clientSecret"],
            expires_at=data["expiresAt"],
        )


@dataclass
class EnvelopeSessionSummary:
    """Summary of a session within an envelope."""
    session_id: str
    transaction_id: str
    signer_index: int
    signer_name: str
    status: str
    completed_at: str | None = None
    evidence_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvelopeSessionSummary:
        return cls(
            session_id=data["sessionId"],
            transaction_id=data["transactionId"],
            signer_index=data["signerIndex"],
            signer_name=data["signerName"],
            status=data["status"],
            completed_at=data.get("completedAt"),
            evidence_id=data.get("evidenceId"),
        )


@dataclass
class EnvelopeDetail:
    """Full envelope details."""
    envelope_id: str
    status: str
    signing_mode: str
    total_signers: int
    added_sessions: int
    completed_sessions: int
    document_hash: str
    sessions: list[EnvelopeSessionSummary]
    created_at: str
    updated_at: str
    expires_at: str
    combined_signed_pdf_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvelopeDetail:
        return cls(
            envelope_id=data["envelopeId"],
            status=data["status"],
            signing_mode=data["signingMode"],
            total_signers=data["totalSigners"],
            added_sessions=data["addedSessions"],
            completed_sessions=data["completedSessions"],
            document_hash=data["documentHash"],
            sessions=[EnvelopeSessionSummary.from_dict(s) for s in data.get("sessions", [])],
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
            expires_at=data["expiresAt"],
            combined_signed_pdf_url=data.get("combinedSignedPdfUrl"),
        )


@dataclass
class CombinedStampResponse:
    """Response from generating/retrieving combined stamp PDF."""
    envelope_id: str
    download_url: str
    expires_in: int
    signer_count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CombinedStampResponse:
        return cls(
            envelope_id=data["envelopeId"],
            download_url=data["downloadUrl"],
            expires_in=data["expiresIn"],
            signer_count=data["signerCount"],
        )
