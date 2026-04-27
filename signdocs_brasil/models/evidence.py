"""Evidence and verification data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EvidenceSigner:
    """Signer information within evidence."""

    name: str
    user_external_id: str
    cpf: str | None = None
    cnpj: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceSigner:
        return cls(
            name=data["name"],
            user_external_id=data["userExternalId"],
            cpf=data.get("cpf"),
            cnpj=data.get("cnpj"),
        )


@dataclass
class EvidenceDocument:
    """Document information within evidence."""

    hash: str
    filename: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceDocument:
        return cls(
            hash=data["hash"],
            filename=data["filename"],
        )


@dataclass
class EvidenceStep:
    """A step record within evidence."""

    type: str
    status: str
    completed_at: str | None = None
    result: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceStep:
        return cls(
            type=data["type"],
            status=data["status"],
            completed_at=data.get("completedAt"),
            result=data.get("result"),
        )


@dataclass
class Evidence:
    """Complete evidence record for a transaction."""

    tenant_id: str
    transaction_id: str
    evidence_id: str
    status: str
    signer: EvidenceSigner
    steps: list[EvidenceStep]
    created_at: str
    document: EvidenceDocument | None = None
    completed_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Evidence:
        return cls(
            tenant_id=data["tenantId"],
            transaction_id=data["transactionId"],
            evidence_id=data["evidenceId"],
            status=data["status"],
            signer=EvidenceSigner.from_dict(data["signer"]),
            steps=[EvidenceStep.from_dict(s) for s in data.get("steps", [])],
            created_at=data["createdAt"],
            document=(
                EvidenceDocument.from_dict(data["document"]) if data.get("document") else None
            ),
            completed_at=data.get("completedAt"),
        )


@dataclass
class VerificationSigner:
    """Signer information within a verification response."""

    display_name: str
    cpf_cnpj: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationSigner:
        return cls(
            display_name=data["displayName"],
            cpf_cnpj=data.get("cpfCnpj"),
        )


@dataclass
class VerificationResponse:
    """Response from verifying evidence."""

    evidence_id: str
    status: str
    transaction_id: str
    purpose: str
    document_hash: str
    evidence_hash: str
    policy: str
    steps: list[dict[str, Any]]
    signer: VerificationSigner
    tenant_name: str
    created_at: str
    completed_at: str | None = None
    tenant_cnpj: str | None = None
    envelope_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationResponse:
        return cls(
            evidence_id=data["evidenceId"],
            status=data["status"],
            transaction_id=data["transactionId"],
            purpose=data["purpose"],
            document_hash=data["documentHash"],
            evidence_hash=data["evidenceHash"],
            policy=data["policy"],
            steps=data.get("steps", []),
            signer=VerificationSigner.from_dict(data["signer"]),
            tenant_name=data["tenantName"],
            created_at=data["createdAt"],
            completed_at=data.get("completedAt"),
            tenant_cnpj=data.get("tenantCnpj"),
            envelope_id=data.get("envelopeId"),
        )


@dataclass
class VerificationDownloadItem:
    """A single download entry with URL and filename."""

    url: str
    filename: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationDownloadItem:
        return cls(
            url=data["url"],
            filename=data["filename"],
        )

    @classmethod
    def from_optional(cls, data: dict[str, Any] | None) -> VerificationDownloadItem | None:
        if data is None:
            return None
        return cls.from_dict(data)


@dataclass
class VerificationDownloads:
    """Nested download URLs for verification artifacts.

    Attributes:
        original_document: Original document uploaded by the client. Only
            present after the transaction reaches ``COMPLETED`` (otherwise
            ``None``).
        evidence_pack: Evidence pack (``.p7m``).
        final_pdf: Final PDF with visual signature stamp.
        signed_signature: Detached PKCS#7 / CMS (``.p7s``) for digital-cert
            signing of non-PDF documents. Only emitted by the API for
            **standalone signing sessions** (single-signer); always ``None``
            for evidences that belong to a multi-signer envelope — use
            :meth:`VerificationResource.verify_envelope` to fetch the
            consolidated envelope-level ``.p7s`` instead.
    """

    original_document: VerificationDownloadItem | None
    evidence_pack: VerificationDownloadItem | None
    final_pdf: VerificationDownloadItem | None
    signed_signature: VerificationDownloadItem | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationDownloads:
        return cls(
            original_document=VerificationDownloadItem.from_optional(data.get("originalDocument")),
            evidence_pack=VerificationDownloadItem.from_optional(data.get("evidencePack")),
            final_pdf=VerificationDownloadItem.from_optional(data.get("finalPdf")),
            signed_signature=VerificationDownloadItem.from_optional(data.get("signedSignature")),
        )


@dataclass
class VerificationDownloadsResponse:
    """Download URLs for verification artifacts."""

    evidence_id: str
    downloads: VerificationDownloads

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationDownloadsResponse:
        return cls(
            evidence_id=data["evidenceId"],
            downloads=VerificationDownloads.from_dict(data["downloads"]),
        )


@dataclass
class EnvelopeVerificationSigner:
    """A single signer entry within an envelope verification response."""

    signer_index: int
    display_name: str
    status: str
    cpf_cnpj: str | None = None
    policy_profile: str | None = None
    evidence_id: str | None = None
    completed_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvelopeVerificationSigner:
        return cls(
            signer_index=int(data["signerIndex"]),
            display_name=data["displayName"],
            status=data["status"],
            cpf_cnpj=data.get("cpfCnpj"),
            policy_profile=data.get("policyProfile"),
            evidence_id=data.get("evidenceId"),
            completed_at=data.get("completedAt"),
        )


@dataclass
class EnvelopeVerificationDownloads:
    """Consolidated download URLs for an envelope.

    Attributes:
        combined_signed_pdf: PDF with all signatures embedded (PDF
            envelopes only).
        consolidated_signature: Consolidated PKCS#7 / CMS detached
            (``.p7s``) containing every signer's ``SignerInfo`` (non-PDF
            envelopes only). Promoted on completion of the final signer.
    """

    combined_signed_pdf: VerificationDownloadItem | None = None
    consolidated_signature: VerificationDownloadItem | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvelopeVerificationDownloads:
        return cls(
            combined_signed_pdf=VerificationDownloadItem.from_optional(data.get("combinedSignedPdf")),
            consolidated_signature=VerificationDownloadItem.from_optional(data.get("consolidatedSignature")),
        )


@dataclass
class EnvelopeVerificationResponse:
    """Public verification response for a multi-signer envelope."""

    envelope_id: str
    status: str
    signing_mode: str
    total_signers: int
    completed_sessions: int
    document_hash: str
    signers: list[EnvelopeVerificationSigner]
    created_at: str
    tenant_name: str | None = None
    tenant_cnpj: str | None = None
    downloads: EnvelopeVerificationDownloads | None = None
    completed_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvelopeVerificationResponse:
        return cls(
            envelope_id=data["envelopeId"],
            status=data["status"],
            signing_mode=data["signingMode"],
            total_signers=int(data["totalSigners"]),
            completed_sessions=int(data["completedSessions"]),
            document_hash=data["documentHash"],
            signers=[EnvelopeVerificationSigner.from_dict(s) for s in data.get("signers", [])],
            created_at=data["createdAt"],
            tenant_name=data.get("tenantName"),
            tenant_cnpj=data.get("tenantCnpj"),
            downloads=(
                EnvelopeVerificationDownloads.from_dict(data["downloads"])
                if data.get("downloads") is not None
                else None
            ),
            completed_at=data.get("completedAt"),
        )
