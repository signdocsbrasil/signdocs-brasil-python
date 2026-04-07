"""Evidence resource for retrieving transaction evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.evidence import Evidence

if TYPE_CHECKING:
    from .._http_client import HttpClient


class EvidenceResource:
    """Evidence retrieval operations."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get(self, transaction_id: str, *, timeout: int | None = None) -> Evidence:
        """Get the evidence record for a transaction.

        Args:
            transaction_id: The transaction identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            Evidence record with signer, steps, and document details.
        """
        data = self._http.request(
            "GET",
            f"/v1/transactions/{transaction_id}/evidence",
            timeout=timeout,
        )
        return Evidence.from_dict(data)
