"""Step resource for listing, starting, and completing verification steps."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..models.step import (
    CompleteBiometricMatchRequest,
    CompleteClickRequest,
    CompleteLivenessRequest,
    CompleteOtpRequest,
    StartStepRequest,
    StartStepResponse,
    StepCompleteResponse,
    StepListResponse,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient

# Union type for all complete step request types
CompleteStepRequest = Union[
    CompleteClickRequest,
    CompleteOtpRequest,
    CompleteLivenessRequest,
    CompleteBiometricMatchRequest,
    dict[str, Any],
]


class StepsResource:
    """Step management operations within a transaction."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self, transaction_id: str, *, timeout: int | None = None,
    ) -> StepListResponse:
        """List all steps for a transaction.

        Args:
            transaction_id: The parent transaction ID.
            timeout: Per-request timeout in milliseconds.

        Returns:
            StepListResponse containing the list of steps.
        """
        data = self._http.request(
            "GET",
            f"/v1/transactions/{transaction_id}/steps",
            timeout=timeout,
        )
        return StepListResponse.from_dict(data)

    def start(
        self,
        transaction_id: str,
        step_id: str,
        request: StartStepRequest | None = None,
        *,
        timeout: int | None = None,
    ) -> StartStepResponse:
        """Start a verification step.

        Args:
            transaction_id: The parent transaction ID.
            step_id: The step identifier.
            request: Optional start parameters (e.g. capture mode, OTP channel).
            timeout: Per-request timeout in milliseconds.

        Returns:
            StartStepResponse with session/URL details.
        """
        body = request.to_dict() if request else {}
        data = self._http.request(
            "POST",
            f"/v1/transactions/{transaction_id}/steps/{step_id}/start",
            body=body,
            timeout=timeout,
        )
        return StartStepResponse.from_dict(data)

    def complete(
        self,
        transaction_id: str,
        step_id: str,
        request: CompleteStepRequest | None = None,
        *,
        timeout: int | None = None,
    ) -> StepCompleteResponse:
        """Complete a verification step.

        Args:
            transaction_id: The parent transaction ID.
            step_id: The step identifier.
            request: Completion data appropriate for the step type.
            timeout: Per-request timeout in milliseconds.

        Returns:
            StepCompleteResponse with updated status and result.
        """
        if request is None:
            body: dict[str, Any] = {}
        elif isinstance(request, dict):
            body = request
        else:
            body = request.to_dict()

        data = self._http.request(
            "POST",
            f"/v1/transactions/{transaction_id}/steps/{step_id}/complete",
            body=body,
            timeout=timeout,
        )
        return StepCompleteResponse.from_dict(data)
