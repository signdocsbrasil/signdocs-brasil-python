"""Transaction-related data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

TransactionStatus = Literal[
    "CREATED",
    "DOCUMENT_UPLOADED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
    "EXPIRED",
    "FAILED",
]

StepType = Literal[
    "CLICK_ACCEPT",
    "OTP_CHALLENGE",
    "OTP_VERIFY",
    "BIOMETRIC_LIVENESS",
    "BIOMETRIC_MATCH",
    "DIGITAL_SIGN_A1",
    "SERPRO_IDENTITY_CHECK",
    "DOCUMENT_PHOTO_MATCH",
    "PURPOSE_DISCLOSURE",
]

StepStatus = Literal["PENDING", "STARTED", "COMPLETED", "FAILED"]

PolicyProfile = Literal[
    "CLICK_ONLY",
    "CLICK_PLUS_OTP",
    "BIOMETRIC",
    "BIOMETRIC_PLUS_OTP",
    "DIGITAL_CERTIFICATE",
    "BIOMETRIC_SERPRO",
    "BIOMETRIC_DOCUMENT_FALLBACK",
    "CUSTOM",
]

TransactionPurpose = Literal["DOCUMENT_SIGNATURE", "ACTION_AUTHENTICATION"]

CaptureMode = Literal["BANK_APP", "HOSTED_PAGE"]

OtpChannel = Literal["email", "sms"]

GeolocationSource = Literal["GPS", "IP", "WIFI", "CELL"]


@dataclass
class Geolocation:
    """Geolocation data captured during a step."""

    latitude: float
    longitude: float
    accuracy: float | None = None
    source: GeolocationSource | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Geolocation:
        return cls(
            latitude=data["latitude"],
            longitude=data["longitude"],
            accuracy=data.get("accuracy"),
            source=data.get("source"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
        if self.accuracy is not None:
            result["accuracy"] = self.accuracy
        if self.source is not None:
            result["source"] = self.source
        return result


@dataclass
class Policy:
    """Signing policy configuration."""

    profile: PolicyProfile
    custom_steps: list[StepType] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Policy:
        return cls(
            profile=data["profile"],
            custom_steps=data.get("customSteps"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"profile": self.profile}
        if self.custom_steps is not None:
            result["customSteps"] = self.custom_steps
        return result


@dataclass
class Signer:
    """Signer identity information."""

    name: str
    user_external_id: str
    email: str | None = None
    phone: str | None = None
    display_name: str | None = None
    cpf: str | None = None
    cnpj: str | None = None
    birth_date: str | None = None
    otp_channel: OtpChannel | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Signer:
        return cls(
            name=data["name"],
            user_external_id=data["userExternalId"],
            email=data.get("email"),
            phone=data.get("phone"),
            display_name=data.get("displayName"),
            cpf=data.get("cpf"),
            cnpj=data.get("cnpj"),
            birth_date=data.get("birthDate"),
            otp_channel=data.get("otpChannel"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "userExternalId": self.user_external_id,
        }
        if self.email is not None:
            result["email"] = self.email
        if self.phone is not None:
            result["phone"] = self.phone
        if self.display_name is not None:
            result["displayName"] = self.display_name
        if self.cpf is not None:
            result["cpf"] = self.cpf
        if self.cnpj is not None:
            result["cnpj"] = self.cnpj
        if self.birth_date is not None:
            result["birthDate"] = self.birth_date
        if self.otp_channel is not None:
            result["otpChannel"] = self.otp_channel
        return result


@dataclass
class ActionMetadata:
    """Metadata for action authentication transactions."""

    type: str
    description: str
    reference: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActionMetadata:
        return cls(
            type=data["type"],
            description=data["description"],
            reference=data.get("reference"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": self.type,
            "description": self.description,
        }
        if self.reference is not None:
            result["reference"] = self.reference
        return result


@dataclass
class DigitalSignatureMetadata:
    """Configuration for digital certificate signing."""

    signature_field_name: str | None = None
    signature_reason: str | None = None
    signature_location: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DigitalSignatureMetadata:
        return cls(
            signature_field_name=data.get("signatureFieldName"),
            signature_reason=data.get("signatureReason"),
            signature_location=data.get("signatureLocation"),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.signature_field_name is not None:
            result["signatureFieldName"] = self.signature_field_name
        if self.signature_reason is not None:
            result["signatureReason"] = self.signature_reason
        if self.signature_location is not None:
            result["signatureLocation"] = self.signature_location
        return result


@dataclass
class InlineDocument:
    """Inline document content for transaction creation."""

    content: str
    filename: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"content": self.content}
        if self.filename is not None:
            result["filename"] = self.filename
        return result


@dataclass
class CreateTransactionRequest:
    """Request to create a new transaction."""

    purpose: TransactionPurpose
    policy: Policy
    signer: Signer
    document: InlineDocument | None = None
    action: ActionMetadata | None = None
    digital_signature: DigitalSignatureMetadata | None = None
    document_group_id: str | None = None
    signer_index: int | None = None
    total_signers: int | None = None
    metadata: dict[str, str] | None = None
    expires_in_minutes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "purpose": self.purpose,
            "policy": self.policy.to_dict(),
            "signer": self.signer.to_dict(),
        }
        if self.document is not None:
            result["document"] = self.document.to_dict()
        if self.action is not None:
            result["action"] = self.action.to_dict()
        if self.digital_signature is not None:
            result["digitalSignature"] = self.digital_signature.to_dict()
        if self.document_group_id is not None:
            result["documentGroupId"] = self.document_group_id
        if self.signer_index is not None:
            result["signerIndex"] = self.signer_index
        if self.total_signers is not None:
            result["totalSigners"] = self.total_signers
        if self.metadata is not None:
            result["metadata"] = self.metadata
        if self.expires_in_minutes is not None:
            result["expiresInMinutes"] = self.expires_in_minutes
        return result


@dataclass
class LivenessResult:
    """Biometric liveness check result."""

    confidence: float
    provider: str
    capture_mode: CaptureMode
    compliance_standards: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LivenessResult:
        return cls(
            confidence=data["confidence"],
            provider=data["provider"],
            capture_mode=data["captureMode"],
            compliance_standards=data.get("complianceStandards"),
        )


@dataclass
class MatchResult:
    """Biometric match result."""

    similarity: float
    threshold: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MatchResult:
        return cls(
            similarity=data["similarity"],
            threshold=data["threshold"],
        )


@dataclass
class OtpResult:
    """OTP verification result."""

    verified: bool
    channel: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OtpResult:
        return cls(
            verified=data["verified"],
            channel=data["channel"],
        )


@dataclass
class ClickResult:
    """Click acceptance result."""

    accepted: bool
    text_version: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClickResult:
        return cls(
            accepted=data["accepted"],
            text_version=data["textVersion"],
        )


@dataclass
class DigitalSignatureResult:
    """Digital signature step result."""

    certificate_subject: str
    certificate_serial: str
    certificate_issuer: str
    algorithm: str
    signed_at: str
    signed_pdf_hash: str
    signature_field_name: str
    signed_pdf_s3_key: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DigitalSignatureResult:
        return cls(
            certificate_subject=data["certificateSubject"],
            certificate_serial=data["certificateSerial"],
            certificate_issuer=data["certificateIssuer"],
            algorithm=data["algorithm"],
            signed_at=data["signedAt"],
            signed_pdf_hash=data["signedPdfHash"],
            signature_field_name=data["signatureFieldName"],
            signed_pdf_s3_key=data.get("signedPdfS3Key"),
        )


@dataclass
class PurposeDisclosureResult:
    """Purpose disclosure acknowledgment result."""

    acknowledged: bool
    disclosure_text_hash: str
    disclosure_version: str
    notification_channel: str
    notification_sent_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PurposeDisclosureResult:
        return cls(
            acknowledged=data["acknowledged"],
            disclosure_text_hash=data["disclosureTextHash"],
            disclosure_version=data["disclosureVersion"],
            notification_channel=data["notificationChannel"],
            notification_sent_at=data.get("notificationSentAt"),
        )


GovernmentDatabase = Literal["SERPRO_DATAVALID", "TSE", "IDRC"]


@dataclass
class GovernmentDbValidation:
    """Government database validation result."""

    database: GovernmentDatabase
    validated_at: str
    cpf_hash: str
    biometric_score: float
    cached: bool
    cache_verify_similarity: float | None = None
    cache_expires_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GovernmentDbValidation:
        return cls(
            database=data["database"],
            validated_at=data["validatedAt"],
            cpf_hash=data["cpfHash"],
            biometric_score=data["biometricScore"],
            cached=data["cached"],
            cache_verify_similarity=data.get("cacheVerifySimilarity"),
            cache_expires_at=data.get("cacheExpiresAt"),
        )


@dataclass
class SerproIdentityResult:
    """SERPRO identity check result."""

    valid: bool
    provider: str
    name_match: bool
    birth_date_match: bool
    biometric_match: bool
    biometric_confidence: float
    government_database: GovernmentDatabase | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SerproIdentityResult:
        return cls(
            valid=data["valid"],
            provider=data["provider"],
            name_match=data["nameMatch"],
            birth_date_match=data["birthDateMatch"],
            biometric_match=data["biometricMatch"],
            biometric_confidence=data["biometricConfidence"],
            government_database=data.get("governmentDatabase"),
        )


@dataclass
class BiographicValidation:
    """Biographic data validation from document extraction."""

    name_match: bool | None
    cpf_match: bool | None
    birth_date_match: bool | None
    overall_valid: bool
    matched_fields: list[str]
    unmatched_fields: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BiographicValidation:
        return cls(
            name_match=data.get("nameMatch"),
            cpf_match=data.get("cpfMatch"),
            birth_date_match=data.get("birthDateMatch"),
            overall_valid=data["overallValid"],
            matched_fields=data.get("matchedFields", []),
            unmatched_fields=data.get("unmatchedFields", []),
        )


@dataclass
class DocumentPhotoMatchResult:
    """Document photo match result."""

    document_type: str
    extracted_face_hash: str
    similarity: float
    threshold: float
    face_extraction_confidence: float
    biographic_validation: BiographicValidation | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentPhotoMatchResult:
        return cls(
            document_type=data["documentType"],
            extracted_face_hash=data["extractedFaceHash"],
            similarity=data["similarity"],
            threshold=data["threshold"],
            face_extraction_confidence=data["faceExtractionConfidence"],
            biographic_validation=(
                BiographicValidation.from_dict(data["biographicValidation"])
                if data.get("biographicValidation")
                else None
            ),
        )


@dataclass
class QualityResult:
    """Image quality assessment result."""

    brightness: float
    sharpness: float
    face_area_ratio: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QualityResult:
        return cls(
            brightness=data["brightness"],
            sharpness=data["sharpness"],
            face_area_ratio=data["faceAreaRatio"],
        )


@dataclass
class StepResult:
    """Result data for a completed step."""

    liveness: LivenessResult | None = None
    match: MatchResult | None = None
    otp: OtpResult | None = None
    click: ClickResult | None = None
    purpose_disclosure: PurposeDisclosureResult | None = None
    digital_signature: DigitalSignatureResult | None = None
    serpro_identity: SerproIdentityResult | None = None
    government_db_validation: GovernmentDbValidation | None = None
    geolocation: Geolocation | None = None
    document_photo_match: DocumentPhotoMatchResult | None = None
    quality: QualityResult | None = None
    provider_timestamp: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepResult:
        return cls(
            liveness=LivenessResult.from_dict(data["liveness"]) if data.get("liveness") else None,
            match=MatchResult.from_dict(data["match"]) if data.get("match") else None,
            otp=OtpResult.from_dict(data["otp"]) if data.get("otp") else None,
            click=ClickResult.from_dict(data["click"]) if data.get("click") else None,
            purpose_disclosure=(
                PurposeDisclosureResult.from_dict(data["purposeDisclosure"])
                if data.get("purposeDisclosure")
                else None
            ),
            digital_signature=(
                DigitalSignatureResult.from_dict(data["digitalSignature"])
                if data.get("digitalSignature")
                else None
            ),
            serpro_identity=(
                SerproIdentityResult.from_dict(data["serproIdentity"])
                if data.get("serproIdentity")
                else None
            ),
            government_db_validation=(
                GovernmentDbValidation.from_dict(data["governmentDbValidation"])
                if data.get("governmentDbValidation")
                else None
            ),
            geolocation=(
                Geolocation.from_dict(data["geolocation"])
                if data.get("geolocation")
                else None
            ),
            document_photo_match=(
                DocumentPhotoMatchResult.from_dict(data["documentPhotoMatch"])
                if data.get("documentPhotoMatch")
                else None
            ),
            quality=QualityResult.from_dict(data["quality"]) if data.get("quality") else None,
            provider_timestamp=data.get("providerTimestamp"),
        )


@dataclass
class Step:
    """A verification/signing step within a transaction."""

    tenant_id: str
    transaction_id: str
    step_id: str
    type: StepType
    status: StepStatus
    order: int
    attempts: int
    max_attempts: int
    capture_mode: CaptureMode | None = None
    started_at: str | None = None
    completed_at: str | None = None
    result: StepResult | None = None
    error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Step:
        return cls(
            tenant_id=data["tenantId"],
            transaction_id=data["transactionId"],
            step_id=data["stepId"],
            type=data["type"],
            status=data["status"],
            order=data["order"],
            attempts=data["attempts"],
            max_attempts=data["maxAttempts"],
            capture_mode=data.get("captureMode"),
            started_at=data.get("startedAt"),
            completed_at=data.get("completedAt"),
            result=StepResult.from_dict(data["result"]) if data.get("result") else None,
            error=data.get("error"),
        )


@dataclass
class Transaction:
    """A complete transaction record."""

    tenant_id: str
    transaction_id: str
    status: TransactionStatus
    purpose: TransactionPurpose
    policy: Policy
    signer: Signer
    steps: list[Step]
    expires_at: str
    created_at: str
    updated_at: str
    document_group_id: str | None = None
    signer_index: int | None = None
    total_signers: int | None = None
    metadata: dict[str, str] | None = None
    submission_deadline: str | None = None
    deadline_status: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transaction:
        return cls(
            tenant_id=data["tenantId"],
            transaction_id=data["transactionId"],
            status=data["status"],
            purpose=data["purpose"],
            policy=Policy.from_dict(data["policy"]),
            signer=Signer.from_dict(data["signer"]),
            steps=[Step.from_dict(s) for s in data.get("steps", [])],
            expires_at=data["expiresAt"],
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
            document_group_id=data.get("documentGroupId"),
            signer_index=data.get("signerIndex"),
            total_signers=data.get("totalSigners"),
            metadata=data.get("metadata"),
            submission_deadline=data.get("submissionDeadline"),
            deadline_status=data.get("deadlineStatus"),
        )


@dataclass
class TransactionListResponse:
    """Paginated list of transactions."""

    transactions: list[Transaction]
    count: int
    next_token: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransactionListResponse:
        return cls(
            transactions=[Transaction.from_dict(t) for t in data.get("transactions", [])],
            count=data["count"],
            next_token=data.get("nextToken"),
        )


@dataclass
class TransactionListParams:
    """Parameters for listing transactions."""

    status: TransactionStatus | None = None
    user_external_id: str | None = None
    document_group_id: str | None = None
    limit: int | None = None
    next_token: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def to_query(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.status is not None:
            result["status"] = self.status
        if self.user_external_id is not None:
            result["userExternalId"] = self.user_external_id
        if self.document_group_id is not None:
            result["documentGroupId"] = self.document_group_id
        if self.limit is not None:
            result["limit"] = self.limit
        if self.next_token is not None:
            result["nextToken"] = self.next_token
        if self.start_date is not None:
            result["startDate"] = self.start_date
        if self.end_date is not None:
            result["endDate"] = self.end_date
        return result


@dataclass
class CancelTransactionResponse:
    """Response after cancelling a transaction."""

    transaction_id: str
    status: str
    cancelled_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CancelTransactionResponse:
        return cls(
            transaction_id=data["transactionId"],
            status=data["status"],
            cancelled_at=data["cancelledAt"],
        )


@dataclass
class FinalizeResponse:
    """Response after finalizing a transaction."""

    transaction_id: str
    status: str
    evidence_id: str
    evidence_hash: str
    completed_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FinalizeResponse:
        return cls(
            transaction_id=data["transactionId"],
            status=data["status"],
            evidence_id=data["evidenceId"],
            evidence_hash=data["evidenceHash"],
            completed_at=data["completedAt"],
        )
