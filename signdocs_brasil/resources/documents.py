"""Document resource for upload, presign, confirm, and download operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.document import (
    ConfirmDocumentRequest,
    ConfirmDocumentResponse,
    DocumentUploadResponse,
    DownloadResponse,
    PresignRequest,
    PresignResponse,
    UploadDocumentRequest,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class DocumentsResource:
    """Document management operations within a transaction."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def upload(
        self,
        transaction_id: str,
        request: UploadDocumentRequest,
        *,
        timeout: int | None = None,
    ) -> DocumentUploadResponse:
        """Upload a document inline (base64-encoded content).

        Args:
            transaction_id: The parent transaction ID.
            request: Document content and optional filename.
            timeout: Per-request timeout in milliseconds.

        Returns:
            DocumentUploadResponse with document hash and status.
        """
        data = self._http.request(
            "POST",
            f"/v1/transactions/{transaction_id}/document",
            body=request.to_dict(),
            timeout=timeout,
        )
        return DocumentUploadResponse.from_dict(data)

    def presign(
        self,
        transaction_id: str,
        request: PresignRequest,
        *,
        timeout: int | None = None,
    ) -> PresignResponse:
        """Get a pre-signed URL for direct document upload.

        Args:
            transaction_id: The parent transaction ID.
            request: Content type and filename for the upload.
            timeout: Per-request timeout in milliseconds.

        Returns:
            PresignResponse with upload URL and token.
        """
        data = self._http.request(
            "POST",
            f"/v1/transactions/{transaction_id}/document/presign",
            body=request.to_dict(),
            timeout=timeout,
        )
        return PresignResponse.from_dict(data)

    def confirm(
        self,
        transaction_id: str,
        request: ConfirmDocumentRequest,
        *,
        timeout: int | None = None,
    ) -> ConfirmDocumentResponse:
        """Confirm a pre-signed document upload.

        Args:
            transaction_id: The parent transaction ID.
            request: Upload token from the presign response.
            timeout: Per-request timeout in milliseconds.

        Returns:
            ConfirmDocumentResponse with document hash and status.
        """
        data = self._http.request(
            "POST",
            f"/v1/transactions/{transaction_id}/document/confirm",
            body=request.to_dict(),
            timeout=timeout,
        )
        return ConfirmDocumentResponse.from_dict(data)

    def download(self, transaction_id: str, *, timeout: int | None = None) -> DownloadResponse:
        """Get a download URL for the transaction's document.

        Args:
            transaction_id: The parent transaction ID.
            timeout: Per-request timeout in milliseconds.

        Returns:
            DownloadResponse with pre-signed download URLs.
        """
        data = self._http.request(
            "GET",
            f"/v1/transactions/{transaction_id}/download",
            timeout=timeout,
        )
        return DownloadResponse.from_dict(data)
