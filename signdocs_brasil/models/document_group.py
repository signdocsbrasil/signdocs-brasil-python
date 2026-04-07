"""Document group data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CombinedStampResponse:
    """Response after generating a combined stamp for a document group."""

    group_id: str
    signer_count: int
    download_url: str
    expires_in: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CombinedStampResponse:
        return cls(
            group_id=data["groupId"],
            signer_count=data["signerCount"],
            download_url=data["downloadUrl"],
            expires_in=data["expiresIn"],
        )
