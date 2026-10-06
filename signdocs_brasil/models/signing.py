"""Signing-related data models for digital certificate workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class PrepareSigningRequest:
    """Request to prepare a digital signature."""

    certificate_chain_pems: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"certificateChainPems": self.certificate_chain_pems}


@dataclass
class PrepareSigningResponse:
    """Response with the hash to be signed."""

    signature_request_id: str
    hash_to_sign: str
    hash_algorithm: Literal["SHA-256"]
    signature_algorithm: Literal["RSASSA-PKCS1-v1_5"]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PrepareSigningResponse:
        return cls(
            signature_request_id=data["signatureRequestId"],
            hash_to_sign=data["hashToSign"],
            hash_algorithm=data["hashAlgorithm"],
            signature_algorithm=data["signatureAlgorithm"],
        )


@dataclass
class CompleteSigningRequest:
    """Request to complete a digital signature with the signed hash."""

    signature_request_id: str
    raw_signature_base64: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signatureRequestId": self.signature_request_id,
            "rawSignatureBase64": self.raw_signature_base64,
        }


@dataclass
class SignatureTimestamp:
    """ICP-Brasil signature timestamp (carimbo do tempo) embedded in the signature.

    RFC 3161 token from an accredited ACT; present only for tenants with the feature.
    ``gen_time`` is the time attested by the ACT; ``signed_at`` on the signature
    result remains the SignDocs server time.
    """

    gen_time: str
    tsa_name: str
    serial: str
    policy_oid: str
    token_sha256: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignatureTimestamp:
        return cls(
            gen_time=data["genTime"],
            tsa_name=data["tsaName"],
            serial=data["serial"],
            policy_oid=data["policyOid"],
            token_sha256=data["tokenSha256"],
        )


@dataclass
class CompleteSigningDigitalSignatureResult:
    """Digital signature result nested in the complete signing response.

    ``signed_pdf_hash`` and ``signature_field_name`` are set for PDF documents;
    ``signed_p7s_hash`` for generic (non-PDF) documents.
    """

    certificate_subject: str
    certificate_serial: str
    certificate_issuer: str
    algorithm: str
    signed_at: str
    signed_pdf_hash: str | None = None
    signature_field_name: str | None = None
    signed_p7s_hash: str | None = None
    document_format: str | None = None
    signature_timestamp: SignatureTimestamp | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompleteSigningDigitalSignatureResult:
        ts = data.get("signatureTimestamp")
        return cls(
            certificate_subject=data["certificateSubject"],
            certificate_serial=data["certificateSerial"],
            certificate_issuer=data["certificateIssuer"],
            algorithm=data["algorithm"],
            signed_at=data["signedAt"],
            signed_pdf_hash=data.get("signedPdfHash"),
            signature_field_name=data.get("signatureFieldName"),
            signed_p7s_hash=data.get("signedP7sHash"),
            document_format=data.get("documentFormat"),
            signature_timestamp=SignatureTimestamp.from_dict(ts) if ts else None,
        )


@dataclass
class CompleteSigningResult:
    """Result wrapper for the complete signing response."""

    digital_signature: CompleteSigningDigitalSignatureResult

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompleteSigningResult:
        return cls(
            digital_signature=CompleteSigningDigitalSignatureResult.from_dict(
                data["digitalSignature"]
            ),
        )


@dataclass
class CompleteSigningResponse:
    """Response after completing a digital signature."""

    step_id: str
    status: str
    result: CompleteSigningResult

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompleteSigningResponse:
        return cls(
            step_id=data["stepId"],
            status=data["status"],
            result=CompleteSigningResult.from_dict(data["result"]),
        )
