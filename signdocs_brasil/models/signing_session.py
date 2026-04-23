"""Signing session data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class SignerRequest:
    """Signer information for session creation."""

    name: str
    user_external_id: str
    email: str | None = None
    phone: str | None = None
    cpf: str | None = None
    cnpj: str | None = None
    otp_channel: Literal["email", "sms"] | None = None
    birth_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"name": self.name, "userExternalId": self.user_external_id}
        if self.email is not None:
            d["email"] = self.email
        if self.phone is not None:
            d["phone"] = self.phone
        if self.cpf is not None:
            d["cpf"] = self.cpf
        if self.cnpj is not None:
            d["cnpj"] = self.cnpj
        if self.otp_channel is not None:
            d["otpChannel"] = self.otp_channel
        if self.birth_date is not None:
            d["birthDate"] = self.birth_date
        return d


@dataclass
class PolicyRequest:
    """Policy configuration for session creation."""

    profile: str
    custom_steps: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"profile": self.profile}
        if self.custom_steps is not None:
            d["customSteps"] = self.custom_steps
        return d


@dataclass
class DocumentRequest:
    """Inline document for session creation."""

    content: str
    filename: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"content": self.content}
        if self.filename is not None:
            d["filename"] = self.filename
        return d


@dataclass
class ActionRequest:
    """Action metadata for ACTION_AUTHENTICATION sessions."""

    type: str
    description: str
    reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type, "description": self.description}
        if self.reference is not None:
            d["reference"] = self.reference
        return d


@dataclass
class AppearanceRequest:
    """Appearance configuration for the signing UI."""

    brand_color: str | None = None
    logo_url: str | None = None
    company_name: str | None = None
    background_color: str | None = None
    text_color: str | None = None
    button_text_color: str | None = None
    border_radius: str | None = None
    header_style: Literal["full", "minimal", "none"] | None = None
    font_family: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.brand_color is not None:
            d["brandColor"] = self.brand_color
        if self.logo_url is not None:
            d["logoUrl"] = self.logo_url
        if self.company_name is not None:
            d["companyName"] = self.company_name
        if self.background_color is not None:
            d["backgroundColor"] = self.background_color
        if self.text_color is not None:
            d["textColor"] = self.text_color
        if self.button_text_color is not None:
            d["buttonTextColor"] = self.button_text_color
        if self.border_radius is not None:
            d["borderRadius"] = self.border_radius
        if self.header_style is not None:
            d["headerStyle"] = self.header_style
        if self.font_family is not None:
            d["fontFamily"] = self.font_family
        return d


@dataclass
class ReferenceImageRequest:
    """Reference image for biometric matching."""

    content: str  # base64-encoded JPEG

    def to_dict(self) -> dict[str, Any]:
        return {"content": self.content}


@dataclass
class Owner:
    """Identity of the requester creating a signing session or envelope,
    distinct from the signer. When provided, SignDocs automatically:

    1. Emails each signer an invitation with their signing URL — when
       ``signer.email`` differs from ``owner.email`` (case-insensitive).
    2. Emails the owner a completion notification per signer completion
       (and a final "all signed" message for envelopes).

    Omit to keep the traditional behavior: the caller delivers signing
    URLs via their own channels and uses webhooks for completion state.
    """

    email: str | None = None
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.email is not None:
            d["email"] = self.email
        if self.name is not None:
            d["name"] = self.name
        return d


@dataclass
class CreateSigningSessionRequest:
    """Request to create a new signing session."""

    purpose: Literal["DOCUMENT_SIGNATURE", "ACTION_AUTHENTICATION"]
    policy: PolicyRequest
    signer: SignerRequest
    document: DocumentRequest | None = None
    action: ActionRequest | None = None
    return_url: str | None = None
    cancel_url: str | None = None
    metadata: dict[str, str] | None = None
    locale: Literal["pt-BR", "en", "es"] | None = None
    expires_in_minutes: int | None = None
    appearance: AppearanceRequest | None = None
    reference_image: ReferenceImageRequest | None = None
    owner: Owner | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "purpose": self.purpose,
            "policy": self.policy.to_dict(),
            "signer": self.signer.to_dict(),
        }
        if self.document is not None:
            d["document"] = self.document.to_dict()
        if self.action is not None:
            d["action"] = self.action.to_dict()
        if self.return_url is not None:
            d["returnUrl"] = self.return_url
        if self.cancel_url is not None:
            d["cancelUrl"] = self.cancel_url
        if self.metadata is not None:
            d["metadata"] = self.metadata
        if self.locale is not None:
            d["locale"] = self.locale
        if self.expires_in_minutes is not None:
            d["expiresInMinutes"] = self.expires_in_minutes
        if self.appearance is not None:
            d["appearance"] = self.appearance.to_dict()
        if self.reference_image is not None:
            d["referenceImage"] = self.reference_image.to_dict()
        if self.owner is not None:
            owner_dict = self.owner.to_dict()
            if owner_dict:
                d["owner"] = owner_dict
        return d


@dataclass
class SigningSession:
    """A signing session returned from the API."""

    session_id: str
    transaction_id: str
    status: str
    url: str
    client_secret: str
    expires_at: str
    created_at: str
    invite_sent: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SigningSession:
        return cls(
            session_id=data["sessionId"],
            transaction_id=data["transactionId"],
            status=data["status"],
            url=data["url"],
            client_secret=data["clientSecret"],
            expires_at=data["expiresAt"],
            created_at=data["createdAt"],
            invite_sent=data.get("inviteSent"),
        )


@dataclass
class SigningSessionStatus:
    """Lightweight session status for polling."""

    session_id: str
    transaction_id: str
    status: str
    completed_at: str | None = None
    evidence_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SigningSessionStatus:
        return cls(
            session_id=data["sessionId"],
            transaction_id=data["transactionId"],
            status=data["status"],
            completed_at=data.get("completedAt"),
            evidence_id=data.get("evidenceId"),
        )


@dataclass
class CancelSigningSessionResponse:
    """Response after cancelling a signing session."""

    session_id: str
    transaction_id: str
    status: str
    cancelled_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CancelSigningSessionResponse:
        return cls(
            session_id=data["sessionId"],
            transaction_id=data["transactionId"],
            status=data["status"],
            cancelled_at=data["cancelledAt"],
        )


@dataclass
class SigningSessionListItem:
    """A session in a list response."""

    session_id: str
    transaction_id: str
    status: str
    created_at: str
    expires_at: str
    locale: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SigningSessionListItem:
        return cls(
            session_id=data["sessionId"],
            transaction_id=data["transactionId"],
            status=data["status"],
            created_at=data["createdAt"],
            expires_at=data["expiresAt"],
            locale=data.get("locale", "pt-BR"),
        )


@dataclass
class ListSigningSessionsResponse:
    """Response from list signing sessions."""

    sessions: list[SigningSessionListItem]
    next_cursor: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ListSigningSessionsResponse:
        return cls(
            sessions=[SigningSessionListItem.from_dict(s) for s in data.get("sessions", [])],
            next_cursor=data.get("nextCursor"),
        )


@dataclass
class ListSigningSessionsParams:
    """Parameters for listing signing sessions."""

    status: str = "ACTIVE"
    limit: int = 20
    cursor: str | None = None


@dataclass
class Geolocation:
    """Geographic coordinates captured during a signing step."""

    latitude: float | None = None
    longitude: float | None = None
    accuracy: float | None = None
    source: Literal["GPS", "IP", "WIFI", "CELL"] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.latitude is not None:
            d["latitude"] = self.latitude
        if self.longitude is not None:
            d["longitude"] = self.longitude
        if self.accuracy is not None:
            d["accuracy"] = self.accuracy
        if self.source is not None:
            d["source"] = self.source
        return d


@dataclass
class AdvanceSessionRequest:
    """Request to advance a signing session step."""

    action: Literal[
        "accept",
        "verify_otp",
        "resend_otp",
        "start_liveness",
        "complete_liveness",
        "prepare_signing",
        "complete_signing",
    ]
    otp_code: str | None = None
    liveness_session_id: str | None = None
    certificate_chain_pems: list[str] | None = None
    signature_request_id: str | None = None
    raw_signature_base64: str | None = None
    geolocation: Geolocation | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"action": self.action}
        if self.otp_code is not None:
            d["otpCode"] = self.otp_code
        if self.liveness_session_id is not None:
            d["livenessSessionId"] = self.liveness_session_id
        if self.certificate_chain_pems is not None:
            d["certificateChainPems"] = self.certificate_chain_pems
        if self.signature_request_id is not None:
            d["signatureRequestId"] = self.signature_request_id
        if self.raw_signature_base64 is not None:
            d["rawSignatureBase64"] = self.raw_signature_base64
        if self.geolocation is not None:
            d["geolocation"] = self.geolocation.to_dict()
        return d


@dataclass
class AdvanceSessionStep:
    """A step within an advance session response."""

    step_id: str
    type: str
    status: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdvanceSessionStep:
        return cls(
            step_id=data["stepId"],
            type=data["type"],
            status=data.get("status"),
        )


@dataclass
class SandboxData:
    """Sandbox-only data returned in HML environment."""

    otp_code: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SandboxData:
        return cls(otp_code=data.get("otpCode"))


@dataclass
class AdvanceSessionResponse:
    """Response after advancing a signing session step."""

    session_id: str
    status: str
    current_step: AdvanceSessionStep | None = None
    next_step: AdvanceSessionStep | None = None
    evidence_id: str | None = None
    redirect_url: str | None = None
    completed_at: str | None = None
    hosted_url: str | None = None
    liveness_session_id: str | None = None
    signature_request_id: str | None = None
    hash_to_sign: str | None = None
    hash_algorithm: str | None = None
    signature_algorithm: str | None = None
    sandbox: SandboxData | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdvanceSessionResponse:
        current_step = None
        if data.get("currentStep") is not None:
            current_step = AdvanceSessionStep.from_dict(data["currentStep"])
        next_step = None
        if data.get("nextStep") is not None:
            next_step = AdvanceSessionStep.from_dict(data["nextStep"])
        sandbox = None
        if data.get("sandbox") is not None:
            sandbox = SandboxData.from_dict(data["sandbox"])
        return cls(
            session_id=data["sessionId"],
            status=data["status"],
            current_step=current_step,
            next_step=next_step,
            evidence_id=data.get("evidenceId"),
            redirect_url=data.get("redirectUrl"),
            completed_at=data.get("completedAt"),
            hosted_url=data.get("hostedUrl"),
            liveness_session_id=data.get("livenessSessionId"),
            signature_request_id=data.get("signatureRequestId"),
            hash_to_sign=data.get("hashToSign"),
            hash_algorithm=data.get("hashAlgorithm"),
            signature_algorithm=data.get("signatureAlgorithm"),
            sandbox=sandbox,
        )


@dataclass
class BootstrapSigner:
    """Masked signer info in a session bootstrap response."""

    name: str
    masked_email: str | None = None
    masked_cpf: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BootstrapSigner:
        return cls(
            name=data["name"],
            masked_email=data.get("maskedEmail"),
            masked_cpf=data.get("maskedCpf"),
        )


@dataclass
class BootstrapStep:
    """A step in a session bootstrap response."""

    step_id: str
    type: str
    status: str
    order: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BootstrapStep:
        return cls(
            step_id=data["stepId"],
            type=data["type"],
            status=data["status"],
            order=data["order"],
        )


@dataclass
class BootstrapDocument:
    """Document info in a session bootstrap response."""

    presigned_url: str | None = None
    filename: str | None = None
    hash: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BootstrapDocument:
        return cls(
            presigned_url=data.get("presignedUrl"),
            filename=data.get("filename"),
            hash=data.get("hash"),
        )


@dataclass
class ActionMetadata:
    """Action metadata in a session bootstrap response."""

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


@dataclass
class Appearance:
    """Appearance settings in a session bootstrap response."""

    brand_color: str | None = None
    logo_url: str | None = None
    company_name: str | None = None
    background_color: str | None = None
    text_color: str | None = None
    button_text_color: str | None = None
    border_radius: str | None = None
    header_style: str | None = None
    font_family: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Appearance:
        return cls(
            brand_color=data.get("brandColor"),
            logo_url=data.get("logoUrl"),
            company_name=data.get("companyName"),
            background_color=data.get("backgroundColor"),
            text_color=data.get("textColor"),
            button_text_color=data.get("buttonTextColor"),
            border_radius=data.get("borderRadius"),
            header_style=data.get("headerStyle"),
            font_family=data.get("fontFamily"),
        )


@dataclass
class SigningSessionBootstrap:
    """Full session bootstrap data returned by GET /v1/signing-sessions/{sessionId}."""

    session_id: str
    transaction_id: str
    status: str
    purpose: str
    signer: BootstrapSigner
    steps: list[BootstrapStep]
    locale: str
    expires_at: str
    document: BootstrapDocument | None = None
    action: ActionMetadata | None = None
    appearance: Appearance | None = None
    return_url: str | None = None
    cancel_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SigningSessionBootstrap:
        document = None
        if data.get("document") is not None:
            document = BootstrapDocument.from_dict(data["document"])
        action = None
        if data.get("action") is not None:
            action = ActionMetadata.from_dict(data["action"])
        appearance = None
        if data.get("appearance") is not None:
            appearance = Appearance.from_dict(data["appearance"])
        return cls(
            session_id=data["sessionId"],
            transaction_id=data["transactionId"],
            status=data["status"],
            purpose=data["purpose"],
            signer=BootstrapSigner.from_dict(data["signer"]),
            steps=[BootstrapStep.from_dict(s) for s in data.get("steps", [])],
            locale=data["locale"],
            expires_at=data["expiresAt"],
            document=document,
            action=action,
            appearance=appearance,
            return_url=data.get("returnUrl"),
            cancel_url=data.get("cancelUrl"),
        )
