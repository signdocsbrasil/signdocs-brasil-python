"""User enrollment data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EnrollUserRequest:
    """Request to enroll a user with a biometric reference image."""

    image: str
    cpf: str
    source: str = "BANK_PROVIDED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "image": self.image,
            "cpf": self.cpf,
            "source": self.source,
        }


@dataclass
class EnrollUserResponse:
    """Response after enrolling a user."""

    user_external_id: str
    enrollment_hash: str
    enrollment_version: int
    enrollment_source: str
    enrolled_at: str
    cpf: str
    face_confidence: float
    document_image_hash: str | None = None
    extraction_confidence: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnrollUserResponse:
        return cls(
            user_external_id=data["userExternalId"],
            enrollment_hash=data["enrollmentHash"],
            enrollment_version=data["enrollmentVersion"],
            enrollment_source=data["enrollmentSource"],
            enrolled_at=data["enrolledAt"],
            cpf=data["cpf"],
            face_confidence=data["faceConfidence"],
            document_image_hash=data.get("documentImageHash"),
            extraction_confidence=data.get("extractionConfidence"),
        )
