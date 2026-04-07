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
class CompleteSigningDigitalSignatureResult:
    """Digital signature result nested in the complete signing response."""

    certificate_subject: str
    certificate_serial: str
    certificate_issuer: str
    algorithm: str
    signed_at: str
    signed_pdf_hash: str
    signature_field_name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompleteSigningDigitalSignatureResult:
        return cls(
            certificate_subject=data["certificateSubject"],
            certificate_serial=data["certificateSerial"],
            certificate_issuer=data["certificateIssuer"],
            algorithm=data["algorithm"],
            signed_at=data["signedAt"],
            signed_pdf_hash=data["signedPdfHash"],
            signature_field_name=data["signatureFieldName"],
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
