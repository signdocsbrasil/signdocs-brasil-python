"""Step-related request/response data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .transaction import CaptureMode, Geolocation, Step


@dataclass
class StartStepRequest:
    """Request to start a step."""

    capture_mode: CaptureMode | None = None
    otp_channel: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.capture_mode is not None:
            result["captureMode"] = self.capture_mode
        if self.otp_channel is not None:
            result["otpChannel"] = self.otp_channel
        return result


@dataclass
class StartStepResponse:
    """Response after starting a step."""

    step_id: str
    type: str
    status: str
    liveness_session_id: str | None = None
    hosted_url: str | None = None
    message: str | None = None
    otp_code: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StartStepResponse:
        return cls(
            step_id=data["stepId"],
            type=data["type"],
            status=data["status"],
            liveness_session_id=data.get("livenessSessionId"),
            hosted_url=data.get("hostedUrl"),
            message=data.get("message"),
            otp_code=data.get("otpCode"),
        )


@dataclass
class CompleteClickRequest:
    """Request to complete a click-accept step."""

    accepted: bool
    text_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"accepted": self.accepted}
        if self.text_version is not None:
            result["textVersion"] = self.text_version
        return result


@dataclass
class CompleteOtpRequest:
    """Request to complete an OTP verification step."""

    code: str

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code}


@dataclass
class CompleteLivenessRequest:
    """Request to complete a biometric liveness step."""

    liveness_session_id: str
    geolocation: Geolocation | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"livenessSessionId": self.liveness_session_id}
        if self.geolocation is not None:
            result["geolocation"] = self.geolocation.to_dict()
        return result


@dataclass
class ReferenceImage:
    """Reference image for biometric matching."""

    source: str = "BASE64_IMAGE"
    data: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "data": self.data}


@dataclass
class CompleteBiometricMatchRequest:
    """Request to complete a biometric match step."""

    reference_image: ReferenceImage | None = None
    sandbox_similarity: float | None = None
    geolocation: Geolocation | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.reference_image is not None:
            result["referenceImage"] = self.reference_image.to_dict()
        if self.sandbox_similarity is not None:
            result["sandboxSimilarity"] = self.sandbox_similarity
        if self.geolocation is not None:
            result["geolocation"] = self.geolocation.to_dict()
        return result


@dataclass
class CompletePurposeDisclosureRequest:
    """Request to complete a purpose disclosure step."""

    acknowledged: bool

    def to_dict(self) -> dict[str, Any]:
        return {"acknowledged": self.acknowledged}


@dataclass
class CompleteDocumentPhotoMatchRequest:
    """Request to complete a document photo match step."""

    document_image: str
    document_type: str
    geolocation: Geolocation | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "documentImage": self.document_image,
            "documentType": self.document_type,
        }
        if self.geolocation is not None:
            result["geolocation"] = self.geolocation.to_dict()
        return result


# CompleteStepResponse is the same shape as Step
CompleteStepResponse = Step


@dataclass
class StepListResponse:
    """Response containing a list of steps."""

    steps: list[Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepListResponse:
        return cls(
            steps=data.get("steps", []),
        )


@dataclass
class StepCompleteResponse:
    """Response after completing a step."""

    step_id: str
    type: str
    status: str
    attempts: int
    result: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepCompleteResponse:
        return cls(
            step_id=data["stepId"],
            type=data["type"],
            status=data["status"],
            attempts=data["attempts"],
            result=data.get("result"),
        )
