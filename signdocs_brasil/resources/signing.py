"""Signing resource for digital certificate signing workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.signing import (
    CompleteSigningRequest,
    CompleteSigningResponse,
    PrepareSigningRequest,
    PrepareSigningResponse,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class SigningResource:
    """Digital certificate signing operations (A1 certificate workflow)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def prepare(
        self,
        transaction_id: str,
        request: PrepareSigningRequest,
        *,
        timeout: int | None = None,
    ) -> PrepareSigningResponse:
        """Prepare a digital signature by submitting the certificate chain.

        The server returns a hash to be signed by the client's private key.

        Args:
            transaction_id: The parent transaction ID.
            request: Certificate chain PEMs.
            timeout: Per-request timeout in milliseconds.

        Returns:
            PrepareSigningResponse with the hash to sign.
        """
        data = self._http.request(
            "POST",
            f"/v1/transactions/{transaction_id}/signing/prepare",
            body=request.to_dict(),
            timeout=timeout,
        )
        return PrepareSigningResponse.from_dict(data)

    def complete(
        self,
        transaction_id: str,
        request: CompleteSigningRequest,
        *,
        timeout: int | None = None,
    ) -> CompleteSigningResponse:
        """Complete a digital signature by submitting the signed hash.

        Args:
            transaction_id: The parent transaction ID.
            request: Signature request ID and the raw signature (base64).
            timeout: Per-request timeout in milliseconds.

        Returns:
            CompleteSigningResponse with the signature result.
        """
        data = self._http.request(
            "POST",
            f"/v1/transactions/{transaction_id}/signing/complete",
            body=request.to_dict(),
            timeout=timeout,
        )
        return CompleteSigningResponse.from_dict(data)
