"""User enrollment data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


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


#: Advisory reasons a reference photo is usable but weak. A row carrying any of
#: these enrols without complaint today and is exactly what fails face matching
#: later, which is the whole reason the dry run exists.
EnrollmentWarning = Literal[
    "LOW_BRIGHTNESS",
    "LOW_SHARPNESS",
    "FACE_TOO_SMALL",
    "HEAD_TURNED",
]


@dataclass
class FaceQualityMetrics:
    """Rekognition's 0-100 measures for the detected face. Dry run only."""

    brightness: float | None = None
    sharpness: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FaceQualityMetrics:
        return cls(brightness=data.get("brightness"), sharpness=data.get("sharpness"))


@dataclass
class FacePoseMetrics:
    """Head rotation in degrees. Dry run only."""

    yaw: float | None = None
    pitch: float | None = None
    roll: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FacePoseMetrics:
        return cls(yaw=data.get("yaw"), pitch=data.get("pitch"), roll=data.get("roll"))


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
    #: Capture metrics for the stored reference.
    quality: FaceQualityMetrics | None = None
    pose: FacePoseMetrics | None = None
    face_coverage: float | None = None
    #: Quality advisories. Present on a *successful* enrolment too — the photo
    #: is stored either way, and knowing it is weak now beats finding out from a
    #: failed signature months later. Empty when there is nothing to flag.
    warnings: list[str] | None = None

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
            quality=FaceQualityMetrics.from_dict(data["quality"]) if data.get("quality") else None,
            pose=FacePoseMetrics.from_dict(data["pose"]) if data.get("pose") else None,
            face_coverage=data.get("faceCoverage"),
            warnings=data.get("warnings"),
        )


@dataclass
class InspectEnrollmentResponse:
    """Verdict for one candidate photo, from a ``dry_run``.

    ``marginal`` is the one to act on: it would enrol without complaint and is
    exactly what becomes a rejected signature later.
    """

    status: str
    warnings: list[str]
    dry_run: bool = True
    user_external_id: str | None = None
    error: str | None = None
    face_confidence: float | None = None
    quality: FaceQualityMetrics | None = None
    pose: FacePoseMetrics | None = None
    face_coverage: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InspectEnrollmentResponse:
        return cls(
            status=data["status"],
            warnings=data.get("warnings", []),
            dry_run=bool(data.get("dryRun", True)),
            user_external_id=data.get("userExternalId"),
            error=data.get("error"),
            face_confidence=data.get("faceConfidence"),
            quality=FaceQualityMetrics.from_dict(data["quality"]) if data.get("quality") else None,
            pose=FacePoseMetrics.from_dict(data["pose"]) if data.get("pose") else None,
            face_coverage=data.get("faceCoverage"),
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


@dataclass
class BatchEnrollmentResult:
    """One row's outcome.

    ``status`` is ``enrolled``/``failed`` on a real write and
    ``usable``/``marginal``/``rejected`` on a dry run. ``marginal`` is the one to
    act on: it would enrol without complaint today and is exactly what becomes a
    rejected signature later.
    """

    index: int
    status: str
    user_external_id: str | None = None
    error: str | None = None
    enrollment_version: int | None = None
    expires_at: str | None = None
    face_confidence: float | None = None
    quality: FaceQualityMetrics | None = None
    pose: FacePoseMetrics | None = None
    #: Face area as a fraction of the frame, 0-1. Dry run only.
    face_coverage: float | None = None
    #: Advisory reasons a photo is usable but weak. Empty on a clean photo.
    warnings: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchEnrollmentResult:
        return cls(
            index=data["index"],
            status=data["status"],
            user_external_id=data.get("userExternalId"),
            error=data.get("error"),
            enrollment_version=data.get("enrollmentVersion"),
            expires_at=data.get("expiresAt"),
            face_confidence=data.get("faceConfidence"),
            quality=FaceQualityMetrics.from_dict(data["quality"]) if data.get("quality") else None,
            pose=FacePoseMetrics.from_dict(data["pose"]) if data.get("pose") else None,
            face_coverage=data.get("faceCoverage"),
            warnings=data.get("warnings"),
        )


@dataclass
class EnrollUsersBatchResponse:
    """Result of a batch enrollment.

    Partial success is the point, so this comes back ``200`` even when rows
    failed: one unusable photo must not reject the other twenty-four. Read
    ``results``, not the HTTP status.
    """

    submitted: int
    results: list[BatchEnrollmentResult]
    #: Real writes only.
    succeeded: int | None = None
    failed: int | None = None
    #: Dry runs only.
    dry_run: bool | None = None
    usable: int | None = None
    marginal: int | None = None
    rejected: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnrollUsersBatchResponse:
        return cls(
            submitted=data["submitted"],
            results=[BatchEnrollmentResult.from_dict(r) for r in data.get("results", [])],
            succeeded=data.get("succeeded"),
            failed=data.get("failed"),
            dry_run=data.get("dryRun"),
            usable=data.get("usable"),
            marginal=data.get("marginal"),
            rejected=data.get("rejected"),
        )
