"""Document-related data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class UploadDocumentRequest:
    """Request to upload a document inline (base64)."""

    content: str
    filename: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"content": self.content}
        if self.filename is not None:
            result["filename"] = self.filename
        return result


@dataclass
class PresignRequest:
    """Request to get a pre-signed upload URL."""

    content_type: str
    filename: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contentType": self.content_type,
            "filename": self.filename,
        }


@dataclass
class PresignResponse:
    """Pre-signed upload URL response."""

    upload_url: str
    upload_token: str
    s3_key: str
    expires_in: int
    content_type: str
    instructions: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresignResponse:
        return cls(
            upload_url=data["uploadUrl"],
            upload_token=data["uploadToken"],
            s3_key=data["s3Key"],
            expires_in=data["expiresIn"],
            content_type=data["contentType"],
            instructions=data["instructions"],
        )


@dataclass
class ConfirmDocumentRequest:
    """Request to confirm a pre-signed document upload."""

    upload_token: str

    def to_dict(self) -> dict[str, Any]:
        return {"uploadToken": self.upload_token}


@dataclass
class ConfirmDocumentResponse:
    """Response after confirming a document upload."""

    transaction_id: str
    status: str
    document_hash: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfirmDocumentResponse:
        return cls(
            transaction_id=data["transactionId"],
            status=data["status"],
            document_hash=data["documentHash"],
        )


@dataclass
class DocumentUploadResponse:
    """Response after uploading a document."""

    transaction_id: str
    document_hash: str
    status: str
    uploaded_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentUploadResponse:
        return cls(
            transaction_id=data["transactionId"],
            document_hash=data["documentHash"],
            status=data["status"],
            uploaded_at=data["uploadedAt"],
        )


@dataclass
class DownloadResponse:
    """Document download URL response."""

    transaction_id: str
    expires_in: int
    document_hash: str | None = None
    original_url: str | None = None
    signed_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DownloadResponse:
        return cls(
            transaction_id=data["transactionId"],
            expires_in=data["expiresIn"],
            document_hash=data.get("documentHash"),
            original_url=data.get("originalUrl"),
            signed_url=data.get("signedUrl"),
        )
