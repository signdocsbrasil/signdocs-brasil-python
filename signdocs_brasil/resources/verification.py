"""Verification resource for verifying evidence and downloading artifacts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.evidence import (
    EnvelopeVerificationResponse,
    VerificationDownloadsResponse,
    VerificationResponse,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class VerificationResource:
    """Public verification operations (no authentication required)."""

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
