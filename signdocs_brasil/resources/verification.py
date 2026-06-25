"""Verification resource for verifying evidence and downloading artifacts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.evidence import (
    EnvelopeVerificationResponse,
    VerificationDownloadsResponse,
    VerificationResponse,
    VerifyDocumentRequest,
    VerifyDocumentResponse,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class VerificationResource:
    """Verification operations.

    Most methods (``verify``, ``downloads``, ``verify_envelope``) are public
    and require no authentication. ``verify_document`` is the exception: it is
    authenticated and requires production credentials with the
    ``verification:write`` scope.
    """

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def verify(
        self, evidence_id: str, *, timeout: int | None = None,
    ) -> VerificationResponse:
        """Verify an evidence record by its ID.

        This endpoint is public and does not require authentication.

        Args:
            evidence_id: The evidence identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            VerificationResponse with validity status and signer info.
        """
        data = self._http.request(
            "GET",
            f"/v1/verify/{evidence_id}",
            no_auth=True,
            timeout=timeout,
        )
        return VerificationResponse.from_dict(data)

    def downloads(
        self, evidence_id: str, *, timeout: int | None = None,
    ) -> VerificationDownloadsResponse:
        """Get download URLs for evidence artifacts.

        This endpoint is public and does not require authentication.

        Args:
            evidence_id: The evidence identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            VerificationDownloadsResponse with pre-signed download URLs.
        """
        data = self._http.request(
            "GET",
            f"/v1/verify/{evidence_id}/downloads",
            no_auth=True,
            timeout=timeout,
        )
        return VerificationDownloadsResponse.from_dict(data)

    def verify_envelope(
        self, envelope_id: str, *, timeout: int | None = None,
    ) -> EnvelopeVerificationResponse:
        """Verify a multi-signer envelope by its ID.

        Returns the envelope status, the list of signers (each with an
        ``evidence_id`` for drill-down via :meth:`verify`), and consolidated
        download URLs. For non-PDF envelopes signed with digital
        certificates, the consolidated ``.p7s`` containing every signer's
        ``SignerInfo`` is exposed via
        ``downloads.consolidated_signature``.

        This endpoint is public and does not require authentication.

        Args:
            envelope_id: The envelope identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            EnvelopeVerificationResponse describing the envelope.
        """
        data = self._http.request(
            "GET",
            f"/v1/verify/envelope/{envelope_id}",
            no_auth=True,
            timeout=timeout,
        )
        return EnvelopeVerificationResponse.from_dict(data)

    def verify_document(
        self,
        request: VerifyDocumentRequest,
        *,
        timeout: int | None = None,
    ) -> VerifyDocumentResponse:
        """Detect whether a PDF already carries signatures.

        Unlike the other verification methods, this endpoint is
        **authenticated**: it requires a Bearer token with the
        ``verification:write`` scope and runs only against
        **production credentials** (the SDK calls it regardless, but the
        API rejects non-production tenants).

        Args:
            request: The document to verify (base64-encoded PDF + optional
                filename).
            timeout: Per-request timeout in milliseconds.

        Returns:
            VerifyDocumentResponse describing whether the PDF is signed and
            the signatures detected.
        """
        data = self._http.request(
            "POST",
            "/v1/verify/document",
            body=request.to_dict(),
            timeout=timeout,
        )
        return VerifyDocumentResponse.from_dict(data)
