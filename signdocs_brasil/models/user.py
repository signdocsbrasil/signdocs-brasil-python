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


@dataclass
class EnrollmentStatusResponse:
    """Enrollment status.

    The reference image is hard-deleted by S3 lifecycle ``retention_days``
    after enrolment, while the record outlives it by a grace period.
    ``expires_at`` and ``expired`` are what let an integrator run a
    re-enrolment sweep instead of discovering the gap as a 422 mid-signature —
    and the sweep has to happen inside that grace window, because once it
    passes this route answers 404, which is indistinguishable from "never
    enrolled".
    """

    user_external_id: str
    enrollment_source: str
    enrollment_version: int
    enrollment_hash: str
    enrolled_at: str
    #: When the reference image is deleted.
    expires_at: str
    #: True once ``expires_at`` has passed — re-enrol.
    expired: bool
    retention_days: int
    #: CPF is masked: this route is enumerable by user_external_id.
    masked_cpf: str | None = None
    face_confidence: float | None = None
    document_image_hash: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnrollmentStatusResponse:
        return cls(
            user_external_id=data["userExternalId"],
            enrollment_source=data["enrollmentSource"],
            enrollment_version=data["enrollmentVersion"],
            enrollment_hash=data["enrollmentHash"],
            enrolled_at=data["enrolledAt"],
            expires_at=data["expiresAt"],
            expired=bool(data["expired"]),
            retention_days=data["retentionDays"],
            masked_cpf=data.get("maskedCpf"),
            face_confidence=data.get("faceConfidence"),
            document_image_hash=data.get("documentImageHash"),
        )


@dataclass
class DeleteEnrollmentResponse:
    """Result of erasing an enrolment (LGPD art. 18)."""

    user_external_id: str
    deleted: bool
    deleted_at: str
    enrollment_version: int | None = None
    #: Objects removed from storage; every version of each is destroyed.
    objects_deleted: int | None = None
    versions_deleted: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeleteEnrollmentResponse:
        return cls(
            user_external_id=data["userExternalId"],
            deleted=bool(data["deleted"]),
            deleted_at=data["deletedAt"],
            enrollment_version=data.get("enrollmentVersion"),
            objects_deleted=data.get("objectsDeleted"),
            versions_deleted=data.get("versionsDeleted"),
        )
