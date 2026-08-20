"""Signing sessions resource."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Literal

from ..models.signing_session import (
    AdvanceSessionRequest,
    AdvanceSessionResponse,
    CancelSigningSessionResponse,
    CreateSigningSessionRequest,
    ListSigningSessionsParams,
    ListSigningSessionsResponse,
    MintSigningLinkResponse,
    ResendOtpRequest,
    SigningSession,
    SigningSessionBootstrap,
    SigningSessionStatus,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class SigningSessionsResource:
    """Signing session operations (create, status, cancel, list, poll)."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        request: CreateSigningSessionRequest,
        *,
        idempotency_key: str | None = None,
        timeout: int | None = None,
    ) -> SigningSession:
        """Create a new signing session.

        Returns the session URL and clientSecret for widget/redirect integration.

        Args:
            request: Session creation parameters.
            idempotency_key: Optional idempotency key.
            timeout: Per-request timeout in milliseconds.

        Returns:
            SigningSession with session URL and clientSecret.
        """
        data = self._http.request_with_idempotency(
            "POST",
            "/v1/signing-sessions",
            body=request.to_dict(),
            idempotency_key=idempotency_key,
            timeout=timeout,
        )
        return SigningSession.from_dict(data)

    def get_status(
        self,
        session_id: str,
        *,
        timeout: int | None = None,
    ) -> SigningSessionStatus:
        """Get the current status of a signing session.

        Args:
            session_id: The session ID.
            timeout: Per-request timeout in milliseconds.

        Returns:
            SigningSessionStatus with current status.
        """
        data = self._http.request(
            "GET",
            f"/v1/signing-sessions/{session_id}/status",
            timeout=timeout,
        )
        return SigningSessionStatus.from_dict(data)

    def cancel(
        self,
        session_id: str,
        *,
        timeout: int | None = None,
    ) -> CancelSigningSessionResponse:
        """Cancel an active signing session.

        Args:
            session_id: The session ID.
            timeout: Per-request timeout in milliseconds.

        Returns:
            CancelSigningSessionResponse.
        """
        data = self._http.request(
            "POST",
            f"/v1/signing-sessions/{session_id}/cancel",
            timeout=timeout,
        )
        return CancelSigningSessionResponse.from_dict(data)

    def link(
        self,
        session_id: str,
        *,
        timeout: int | None = None,
    ) -> MintSigningLinkResponse:
        """Mint a fresh signing URL for an existing session and return it.

        A signing link is **single-use**: once the signer finishes — or the
        embed token is otherwise consumed — reopening the same URL returns
        ``401 Embed token has been consumed``. This issues a new one without
        creating another transaction and **without consuming quota**. Works for
        standalone and envelope sessions alike.

        ``expires_at`` is inherited from the original session and is not
        extended by this call.

        **Authorises the tenant, not the end user.** The API cannot tell which
        of your users is entitled to this link, so an application whose users
        share one tenant must establish that itself before calling — otherwise
        this becomes a way for one user to obtain another's signing credential.

        Args:
            session_id: The session ID. Must be ``ACTIVE``.
            timeout: Per-request timeout in milliseconds.

        Returns:
            MintSigningLinkResponse.

        Raises:
            ConflictError: The session is not ``ACTIVE``. A link to a finished
                session would authenticate nothing; use
                ``envelopes.combined_stamp()`` or ``transactions.download()``
                to reach the signed document instead.
        """
        data = self._http.request(
            "POST",
            f"/v1/signing-sessions/{session_id}/link",
            timeout=timeout,
        )
        return MintSigningLinkResponse.from_dict(data)

    def list(
        self,
        params: ListSigningSessionsParams | None = None,
        *,
        timeout: int | None = None,
    ) -> ListSigningSessionsResponse:
        """List signing sessions filtered by status.

        Args:
            params: Filter and pagination parameters.
            timeout: Per-request timeout in milliseconds.

        Returns:
            ListSigningSessionsResponse with sessions and optional cursor.
        """
        query: dict[str, str] = {}
        if params is not None:
            query["status"] = params.status
            query["limit"] = str(params.limit)
            if params.cursor is not None:
                query["cursor"] = params.cursor
        else:
            query["status"] = "ACTIVE"

        data = self._http.request(
            "GET",
            "/v1/signing-sessions",
            query=query,
            timeout=timeout,
        )
        return ListSigningSessionsResponse.from_dict(data)

    def get(
        self,
        session_id: str,
        *,
        timeout: int | None = None,
    ) -> SigningSessionBootstrap:
        """Get full bootstrap data for a signing session.

        Used by the embedded signing widget to initialize the UI.

        Args:
            session_id: The session ID.
            timeout: Per-request timeout in milliseconds.

        Returns:
            SigningSessionBootstrap with signer, steps, document, and appearance data.
        """
        data = self._http.request(
            "GET",
            f"/v1/signing-sessions/{session_id}",
            timeout=timeout,
        )
        return SigningSessionBootstrap.from_dict(data)

    def advance(
        self,
        session_id: str,
        request: AdvanceSessionRequest,
        *,
        timeout: int | None = None,
    ) -> AdvanceSessionResponse:
        """Advance a signing session through its steps.

        Supports actions: accept, verify_otp, resend_otp, start_liveness,
        complete_liveness, prepare_signing, complete_signing.

        Args:
            session_id: The session ID.
            request: The advance request with action and optional parameters.
            timeout: Per-request timeout in milliseconds.

        Returns:
            AdvanceSessionResponse with current/next step and session status.
        """
        data = self._http.request(
            "POST",
            f"/v1/signing-sessions/{session_id}/advance",
            body=request.to_dict(),
            timeout=timeout,
        )
        return AdvanceSessionResponse.from_dict(data)

    def resend_otp(
        self,
        session_id: str,
        *,
        channel: Literal["email", "sms"] | None = None,
        timeout: int | None = None,
    ) -> AdvanceSessionResponse:
        """Resend the OTP challenge for a signing session.

        Args:
            session_id: The session ID.
            channel: Optional delivery channel for the resent OTP ("email" or "sms").
                When omitted, the API uses the signer's configured channel.
            timeout: Per-request timeout in milliseconds.

        Returns:
            AdvanceSessionResponse with updated step info.
        """
        body = ResendOtpRequest(channel=channel).to_dict() if channel is not None else None
        data = self._http.request(
            "POST",
            f"/v1/signing-sessions/{session_id}/resend-otp",
            body=body,
            timeout=timeout,
        )
        return AdvanceSessionResponse.from_dict(data)

    def wait_for_completion(
        self,
        session_id: str,
        *,
        poll_interval_ms: int = 3000,
        timeout_ms: int = 300_000,
    ) -> SigningSessionStatus:
        """Poll until the session reaches a terminal state.

        Args:
            session_id: The session ID.
            poll_interval_ms: Polling interval in milliseconds (default 3000).
            timeout_ms: Maximum wait time in milliseconds (default 300000 = 5 min).

        Returns:
            Final SigningSessionStatus.

        Raises:
            TimeoutError: If the session does not reach a terminal state in time.
        """
        start = time.monotonic()
        while (time.monotonic() - start) * 1000 < timeout_ms:
            status = self.get_status(session_id)
            if status.status != "ACTIVE":
                return status
            time.sleep(poll_interval_ms / 1000)

        raise TimeoutError(
            f"Signing session {session_id} did not complete within {timeout_ms}ms"
        )
