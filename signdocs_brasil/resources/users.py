"""Users resource for biometric enrollment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.user import (
    DeleteEnrollmentResponse,
    EnrollmentStatusResponse,
    EnrollUserRequest,
    EnrollUserResponse,
    EnrollUsersBatchResponse,
)

if TYPE_CHECKING:
    from .._http_client import HttpClient


class UsersResource:
    """User management operations."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def enroll(
        self,
        user_external_id: str,
        request: EnrollUserRequest,
        *,
        timeout: int | None = None,
    ) -> EnrollUserResponse:
        """Enroll a user with a biometric reference image.

        Args:
            user_external_id: The external user identifier.
            request: Enrollment data including the reference image.
            timeout: Per-request timeout in milliseconds.

        Returns:
            EnrollUserResponse with enrollment confirmation.
        """
        data = self._http.request(
            "PUT",
            f"/v1/users/{user_external_id}/enrollment",
            body=request.to_dict(),
            timeout=timeout,
        )
        return EnrollUserResponse.from_dict(data)

    def get_enrollment(
        self,
        user_external_id: str,
        *,
        timeout: int | None = None,
    ) -> EnrollmentStatusResponse:
        """Read whether a user is enrolled and, crucially, until when.

        Use it to sweep your user base and re-enrol before ``expired`` flips.
        Nothing warns you on its own beyond the ``ENROLLMENT.EXPIRING``
        webhook, and once the grace window closes this raises NotFound rather
        than reporting an expired enrolment.

        Args:
            user_external_id: The external user identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            EnrollmentStatusResponse with the expiry window.
        """
        data = self._http.request(
            "GET",
            f"/v1/users/{user_external_id}/enrollment",
            timeout=timeout,
        )
        return EnrollmentStatusResponse.from_dict(data)

    def delete_enrollment(
        self,
        user_external_id: str,
        *,
        timeout: int | None = None,
    ) -> DeleteEnrollmentResponse:
        """Erase a user's biometric enrolment (LGPD art. 18).

        Destroys every stored version of the reference image, not just the
        current one, and removes the record. Irreversible.

        Args:
            user_external_id: The external user identifier.
            timeout: Per-request timeout in milliseconds.

        Returns:
            DeleteEnrollmentResponse with what was destroyed.
        """
        data = self._http.request(
            "DELETE",
            f"/v1/users/{user_external_id}/enrollment",
            timeout=timeout,
        )
        return DeleteEnrollmentResponse.from_dict(data)

    def enroll_batch(
        self,
        enrollments: list[dict[str, Any]],
        *,
        dry_run: bool = False,
        timeout: int | None = None,
    ) -> EnrollUsersBatchResponse:
        """Enrol up to 25 users in one request.

        The documented cap is 25 rows, but the binding limit is the request
        body — roughly 6MB, and base64 inflates each photo by a third. Keep
        photos under ~175KB (640x640 is ample) to use all 25 slots.

        With ``dry_run`` nothing is persisted: every row is inspected and
        returned with quality metrics, no image reaches storage, and the 90-day
        retention clock never starts. Rekognition's confidence answers "is this
        a face?", not "is this a good reference" — a dark, blurred photo enrols
        happily at 99.99 confidence and fails face matching months later. A dry
        run surfaces that while the batch is still in front of you.

        Args:
            enrollments: Rows, each with userExternalId, image and cpf.
            dry_run: Inspect without writing.
            timeout: Per-request timeout in milliseconds.

        Returns:
            EnrollUsersBatchResponse. Read ``results`` — a batch with failed
            rows is still HTTP 200.
        """
        body: dict[str, Any] = {"enrollments": enrollments}
        if dry_run:
            body["dryRun"] = True
        data = self._http.request(
            "POST",
            "/v1/users/enrollments",
            body=body,
            timeout=timeout,
        )
        return EnrollUsersBatchResponse.from_dict(data)
