"""Envelopes resource for multi-signer envelope workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.envelope import (
    AddEnvelopeSessionRequest,
    CombinedStampResponse,
    CreateEnvelopeRequest,
    Envelope,
    EnvelopeDetail,
    EnvelopeSession,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class EnvelopesResource:
    """Envelope operations (create, get, add session)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        request: CreateEnvelopeRequest,
        *,
        idempotency_key: str | None = None,
        timeout: int | None = None,
    ) -> Envelope:
        """Create a new envelope for multi-signer signing.

        Args:
            request: Envelope creation parameters.
            idempotency_key: Optional idempotency key.
            timeout: Per-request timeout in milliseconds.

        Returns:
            Envelope with envelope ID and status.
        """
        data = self._http.request_with_idempotency(
            "POST",
            "/v1/envelopes",
            body=request.to_dict(),
            idempotency_key=idempotency_key,
            timeout=timeout,
        )
        return Envelope.from_dict(data)

    def get(
        self,
        envelope_id: str,
        *,
        timeout: int | None = None,
    ) -> EnvelopeDetail:
        """Get envelope details including session summaries.

        Args:
            envelope_id: The envelope ID.
            timeout: Per-request timeout in milliseconds.

        Returns:
            EnvelopeDetail with full envelope information.
        """
        data = self._http.request(
            "GET",
            f"/v1/envelopes/{envelope_id}",
            timeout=timeout,
        )
        return EnvelopeDetail.from_dict(data)

    def add_session(
        self,
        envelope_id: str,
        request: AddEnvelopeSessionRequest,
        *,
        timeout: int | None = None,
    ) -> EnvelopeSession:
        """Add a signer session to an envelope.

        Args:
            envelope_id: The envelope ID.
            request: Session parameters for the signer.
            timeout: Per-request timeout in milliseconds.

        Returns:
            EnvelopeSession with session URL and clientSecret.
        """
        data = self._http.request(
            "POST",
            f"/v1/envelopes/{envelope_id}/sessions",
            body=request.to_dict(),
            timeout=timeout,
        )
        return EnvelopeSession.from_dict(data)

    def combined_stamp(
        self,
        envelope_id: str,
        *,
        timeout: int | None = None,
    ) -> CombinedStampResponse:
        """Generate or retrieve the combined stamp PDF for a completed envelope.

        Args:
            envelope_id: The envelope ID.
            timeout: Per-request timeout in milliseconds.

        Returns:
            CombinedStampResponse with download URL.
        """
        data = self._http.request(
            "POST",
            f"/v1/envelopes/{envelope_id}/combined-stamp",
            timeout=timeout,
        )
        return CombinedStampResponse.from_dict(data)
