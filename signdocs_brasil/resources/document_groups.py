"""Document groups resource for multi-signer document workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.document_group import CombinedStampResponse

if TYPE_CHECKING:
    from .._http_client import HttpClient


class DocumentGroupsResource:
    """Document group operations."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def combined_stamp(
        self, document_group_id: str, *, timeout: int | None = None,
    ) -> CombinedStampResponse:
        """Generate a combined stamp for all signatures in a document group.

        Args:
            document_group_id: The document group identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            CombinedStampResponse with the stamped document URL.
        """
        data = self._http.request(
            "POST",
            f"/v1/document-groups/{document_group_id}/combined-stamp",
            timeout=timeout,
        )
        return CombinedStampResponse.from_dict(data)
