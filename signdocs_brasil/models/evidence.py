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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationSigner:
        return cls(display_name=data["displayName"])


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


@dataclass
class VerificationDownloads:
    """Nested download URLs for verification artifacts."""

    evidence_pack: VerificationDownloadItem
    signed_pdf: VerificationDownloadItem
    final_pdf: VerificationDownloadItem

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VerificationDownloads:
        return cls(
            evidence_pack=VerificationDownloadItem.from_dict(data["evidencePack"]),
            signed_pdf=VerificationDownloadItem.from_dict(data["signedPdf"]),
            final_pdf=VerificationDownloadItem.from_dict(data["finalPdf"]),
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
